from fastapi import HTTPException, status


class InvalidCredentialsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}, # заголовок обязателен по спецификации OAuth2
        )

class UnauthorizedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in",
            headers={"WWW-Authenticate": "Bearer"}, # заголовок обязателен по спецификации OAuth2
        )

class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Log in again please",
            headers={"WWW-Authenticate": "Bearer"}, # заголовок обязателен по спецификации OAuth2
        )
        
class ParticularUserNotFoundException(HTTPException):
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
            headers={"WWW-Authenticate": "Bearer"}, # заголовок обязателен по спецификации OAuth2
        )