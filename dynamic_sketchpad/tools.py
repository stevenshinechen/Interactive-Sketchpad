from enum import StrEnum


class Tool(StrEnum):
    CODE_INTERPRETER = "code_interpreter"
    FILE_SEARCH = "file_search"

    def to_dict(self):
        return {"type": self.value}
