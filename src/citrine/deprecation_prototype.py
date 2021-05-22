import ast
import os
from typing import List, Dict


class VersionNumber:

    def __init__(self, version: str):
        self.version = version
        entries = version.split('.')
        if len(entries) != 3:
            raise ValueError(f"version {version} is not of the form major.minor.patch")
        try:
            self.major = int(entries[0])
            self.minor = int(entries[1])
            self.patch = int(entries[2])
        except ValueError:
            raise ValueError(f"version {version} must be parseable as a series of integers")

    def __eq__(self, other):
        return self.major == other.major and self.minor == other.minor and self.patch == other.patch

    def __lt__(self, other):
        if self.major < other.major:
            return True
        elif self.major == other.major:
            if self.minor < other.minor:
                return True
            elif self.minor == other.minor:
                if self.patch < other.patch:
                    return True
        return False

    def __ge__(self, other):
        return not self.__lt__(other)


def get_deprecated_dict(decorator: ast.AST) -> Dict[str, str]:
    keyword_dict = None
    if isinstance(decorator, ast.Call):
        try:
            func: ast.Name = decorator.func
            name: str = func.id
            if name == "deprecated":
                keyword_dict = dict()
                keywords: List[ast.keyword] = decorator.keywords
                for keyword in keywords:
                    try:
                        arg = keyword.arg
                        value = keyword.value.s
                        keyword_dict[arg] = value
                    except AttributeError:
                        pass
        except AttributeError:
            pass
    return keyword_dict


def check_deprecation(deprecated_dict: Dict[str, str], name: str):
    if "deprecated_in" not in deprecated_dict or "removed_in" not in deprecated_dict:
        return f"Deprecation of {name} must specify when deprecated and when removed"
    try:
        removed_version = VersionNumber(deprecated_dict["removed_in"])
        current_version = VersionNumber("1.1.0")
        if current_version >= removed_version:
            return f"{name} is supposed to be removed in version {removed_version.version}, but current version is {current_version.version}"
    except ValueError as e:
        return f"Cannot parse deprecation of {name}, encountered error {e}"


def get_deprecations(node: ast.AST):
    try:
        decorators = node.decorator_list
        this_name = node.name
        if isinstance(decorators, list):
            for decorator in decorators:
                deprecated_dict = get_deprecated_dict(decorator)
                if deprecated_dict is not None:
                    return check_deprecation(deprecated_dict, this_name)
    except AttributeError:
        pass


RELEVANT_NODE_TYPES = (ast.Module, ast.ClassDef, ast.FunctionDef)


def iter_relevant_children(node: ast.AST):
    for name, field in ast.iter_fields(node):
        if isinstance(field, RELEVANT_NODE_TYPES):
            yield field
        elif isinstance(field, list):
            for item in field:
                if isinstance(item, RELEVANT_NODE_TYPES):
                    yield item


def walk_deprecations(node: ast.AST):
    from collections import deque
    todo = deque([node])
    while todo:
        node = todo.popleft()
        todo.extend(iter_relevant_children(node))
        yield get_deprecations(node)


if __name__ == "__main__":
    path = os.path.abspath("informatics/predictors/expression_predictor.py")
    with open(path) as source:
        tree = ast.parse(source.read())
        deprecation_generator = walk_deprecations(tree)
        all_deps = list(deprecation_generator)
        print("done")
