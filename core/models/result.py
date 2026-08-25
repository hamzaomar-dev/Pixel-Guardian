from dataclasses import dataclass
from typing import Generic,TypeVar


T=TypeVar("T")


@dataclass(slots=True)

class ServiceResult(Generic[T]):

    """نتيجة موحدة لجميع خدمات Pixel Guardian.
    """

    success : bool
    data : T | None = None
    message : str = ""
    error_code:str | None = None
    source : str | None = None


    @classmethod

    def ok(
        cls, 
        data : T,
        message:str = "",
        source : str | None = None,
    ) -> "ServiceResult[T]":
        
        return cls(
            success = True,
            data = data,
            message = message,
            source = source,
        )
    
    @classmethod
    def fail (
        cls,
        message : str,
        error_code:str,
        source:str | None = None,
    )  -> "ServiceResult[T]":
        return cls(
            success=False,
            data=None,
            message=message,
            error_code=error_code,
            source=source,
        )

