# Interactive Sketchpad: An Interactive Multimodal System for Collaborative, Visual Problem-Solving

This repo contains the official code for Interactive Sketchpad, a tutoring system that combines language-based explanations with interactive visualizations to enhance learning.
Built on a pre-trained LMM, Interactive Sketchpad is fine-tuned to provide step-by-step guidance in both text and visuals, enabling natural multimodal
interaction with the student. Accurate and robust diagrams are gen-
erated by incorporating code execution into the reasoning process.

## Introduction
Interactive Sketchpad enhances GPT-4o’s ability to provide step-by-step, visual hints for problem-solving. Given a student query and problem statement, Interactive Sketchpad generates both textual hints and dynamic visual diagrams, allowing students to engage with the problem iteratively. Without Interactive Sketchpad, GPT-4o struggles to offer effective interactive guidance, frequently revealing the answer and not providing any visual aids, whereas Interactive Sketchpad enables a natural, multimodal learning experience that improves conceptual understanding.
![Calculus Teaser](assets/teaser_calculus.png)

Given a multimodal question, Interactive Sketchpad generates a program
to create a visual aid, then uses the visual aid as part of a hint to help the user solve the problem. The visual aid is sent to the
interactive whiteboard which the user can write and draw on before sending the annotated diagram back to receive feedback or
further help.
![Geometry Teaser](assets/teaser_geometry.png)

## Installation
1. Install uv https://docs.astral.sh/uv/getting-started/installation/
2. Run `uv sync` to install dependencies

## Running Interactive Sketchpad
To run interactive sketchpad, do:
`cd interactive_sketchpad`
`uv run uvicorn main:app --host 127.0.0.1 --port 8000`

Then go to the following link:
`http://127.0.0.1:8000/interactive_sketchpad/`
