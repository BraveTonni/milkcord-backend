from pydantic import BaseModel, model_validator


class BaseResponse(BaseModel):
    success: bool


class SuccessResponse(BaseResponse):
    success: bool = True

    @model_validator(mode="after")
    def check_success_is_false(self) -> "SuccessResponse":
        if self.success is not True:
            raise ValueError("success must be True in SuccessResponse")

        return self


class ErrorResponse(BaseResponse):
    success: bool = False
    error: str = "Ошибка не указана"

    @model_validator(mode="after")
    def check_success_is_false(self) -> "ErrorResponse":
        if self.success is not False:
            raise ValueError("success must be False in ErrorResponse")

        return self
