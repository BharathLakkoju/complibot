from ulid import ULID


def new_id(prefix: str) -> str:
    return f"{prefix}_{ULID()}"


def new_tenant_id() -> str:
    return new_id("tnt")


def new_user_id() -> str:
    return new_id("usr")


def new_project_id() -> str:
    return new_id("prj")


def new_document_id() -> str:
    return new_id("doc")


def new_review_id() -> str:
    return new_id("rev")


def new_finding_id() -> str:
    return new_id("fnd")


def new_event_id() -> str:
    return new_id("evt")


def new_decision_id() -> str:
    return new_id("dec")


def new_comment_id() -> str:
    return new_id("cmt")
