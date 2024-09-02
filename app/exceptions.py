from fastapi import HTTPException, status


class AuthException(HTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Not enough rights for this request"

    def __init__(
        self,
        status_code: int | None = None,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        if detail is None:
            detail = self.default_detail
        if status_code is None:
            status_code = self.status_code

        super().__init__(status_code=status_code, detail=detail, headers=headers)
