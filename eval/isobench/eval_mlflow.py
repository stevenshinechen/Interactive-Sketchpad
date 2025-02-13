import asyncio
import logging
import sys
from functools import partial
from typing import Callable

import mlflow
import pandas as pd
from tqdm.asyncio import tqdm

from dynamic_sketchpad.dynamic_sketchpad import DynamicSketchpad
from dynamic_sketchpad.llm import LLM
from eval.answer_extractor import extract_answer
from eval.isobench.loader import IsobenchTask, load_isobench_dataset
from eval.isobench.mlflow_utils import with_mlflow_server
from eval.isobench.prompts import get_prompt, get_prompt_template


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(name)s: %(asctime)s] {%(process)d} %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


logger = setup_logging()


def get_eval_data(task: IsobenchTask) -> pd.DataFrame:
    ds = load_isobench_dataset(task)
    eval_data = ds.to_pandas()
    if "image" in eval_data.columns:
        eval_data.drop(columns=["image"], inplace=True)

    eval_data["prompt"] = eval_data.apply(lambda x: get_prompt(x, task), axis=1)
    return eval_data


def llm_model_predict(llm_str: str):
    llm = LLM(llm_str=llm_str)
    return partial(
        predict,
        output_generator=lambda prompts, _: asyncio.run(
            llm.generate_responses(prompts)
        ),
    )


def dynamic_sketchpad_predict(llm_str: str):
    sketchpad = DynamicSketchpad(llm_str=llm_str)

    def generate_responses(prompts: list[str], df: pd.DataFrame) -> list[str]:
        all_messages = sketchpad.invoke_all(*prompts)
        responses = [
            sketchpad.messages_to_string(messages) for messages in all_messages
        ]

        images = [sketchpad.messages_to_images(messages) for messages in all_messages]
        for test_id, images in zip(df["id"], images):
            for i, image in enumerate(images):
                mlflow.log_image(image, artifact_file=f"{test_id}/images/{i}.png")
        mlflow.set_tag("tool", "dynamic_sketchpad")
        mlflow.log_param("instruction_hash", hash(sketchpad.assistant.instructions))
        mlflow.log_text(
            sketchpad.assistant.instructions, artifact_file="instructions.txt"
        )
        print(f"Generated responses: {responses}")
        return responses

    return partial(
        predict,
        output_generator=lambda prompts, df: generate_responses(prompts, df),
    )


def predict(
    df: pd.DataFrame, output_generator: Callable[[pd.DataFrame], list[str]]
) -> list[str]:
    prompts = df["prompt"].tolist()
    outputs = output_generator(prompts, df)
    answers = asyncio.run(
        tqdm.gather(
            *[
                extract_answer(question=prompt, response=output)
                for prompt, output in zip(prompts, outputs)
            ],
            desc="Extracting answers",
        )
    )

    logger.info(f"Extracted answers:\n{answers}")

    for test_id, output in zip(df["id"], outputs):
        mlflow.log_text(output, artifact_file=f"{test_id}.txt")

    return answers


def evaluate_llm_on_isobench(llm_str: str, task: IsobenchTask):
    predict = llm_model_predict(llm_str)
    evaluate_model_on_isobench(predict, llm_str, task)


def evaluate_dynamic_sketchpad_on_isobench(llm_str: str, task: IsobenchTask):
    predict = dynamic_sketchpad_predict(llm_str)
    evaluate_model_on_isobench(predict, llm_str, task)


def evaluate_model_on_isobench(model, llm_str: str, task: IsobenchTask):
    eval_data = get_eval_data(task)
    run_evaluation(model, eval_data, llm_str, task)


def run_evaluation(model, eval_data: pd.DataFrame, llm_str: str, task: IsobenchTask):
    mlflow.set_experiment(f"IsoBench: {task}")
    with mlflow.start_run() as run:
        mlflow.log_param("task", task)
        mlflow.log_param("llm_str", llm_str)
        prompt_template = get_prompt_template(task)
        mlflow.log_param("prompt_template_hash", hash(prompt_template))
        mlflow.log_text(prompt_template, artifact_file="prompt_template.txt")

        results = mlflow.evaluate(
            model=model,
            data=eval_data,
            targets="label",
            model_type="question-answering",
            evaluators=["default"],
        )

        print(f"Evaluation results: {results.metrics}")


if __name__ == "__main__":
    with with_mlflow_server():
        evaluate_dynamic_sketchpad_on_isobench(
            "gpt-4o-2024-11-20", IsobenchTask.MATH_CONVEXITY
        )
        # evaluate_llm_on_isobench("gpt-4o-2024-11-20", IsobenchTask.GRAPH_CONNECTIVITY)
        # evaluate_llm_on_isobench("gpt-4o-2024-11-20", IsobenchTask.GRAPH_ISOMORPHISM)
        # evaluate_llm_on_isobench("gpt-4o-2024-11-20", IsobenchTask.WINNER_ID)
        # evaluate_llm_on_isobench("gpt-4o-2024-11-20", IsobenchTask.MATH_BREAKPOINT)
