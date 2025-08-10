from pydantic import BaseModel, EmailStr, constr

class UserCreateSchema(BaseModel):
    name: str
    email: EmailStr
    password: constr(min_length=8)

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequestSchema(BaseModel):
    email: EmailStr

class PasswordResetSchema(BaseModel):
    token: str
    new_password: constr(min_length=8)