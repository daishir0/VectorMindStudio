from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
import re


class TemplateStatus(str, Enum):
    """テンプレートステータス"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class VariableType(str, Enum):
    """変数タイプ"""
    STRING = "string"
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    LIST = "list"


class TemplateVariable(BaseModel):
    """テンプレート変数"""
    name: str = Field(..., min_length=1, max_length=100)
    type: VariableType
    description: str = Field("", max_length=500)
    required: bool = True
    default_value: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def validate_variable_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('Variable name must be a valid identifier')
        return v
    
    def validate_value(self, value: Any) -> bool:
        """値のバリデーション"""
        if value is None:
            return not self.required
        
        # 型チェック
        if self.type == VariableType.STRING and not isinstance(value, str):
            return False
        elif self.type == VariableType.NUMBER and not isinstance(value, (int, float)):
            return False
        elif self.type == VariableType.BOOLEAN and not isinstance(value, bool):
            return False
        elif self.type == VariableType.LIST and not isinstance(value, list):
            return False
        
        # バリデーションルールチェック
        if self.validation_rules:
            if self.type == VariableType.NUMBER:
                min_val = self.validation_rules.get('min')
                max_val = self.validation_rules.get('max')
                if min_val is not None and value < min_val:
                    return False
                if max_val is not None and value > max_val:
                    return False
            
            elif self.type == VariableType.STRING:
                min_length = self.validation_rules.get('min_length')
                max_length = self.validation_rules.get('max_length')
                if min_length is not None and len(value) < min_length:
                    return False
                if max_length is not None and len(value) > max_length:
                    return False
        
        return True


class Template(BaseModel):
    """テンプレートエンティティ"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    content: str = Field(..., min_length=1)
    variables: List[TemplateVariable] = []
    requirements: str = Field("", max_length=2000)
    tags: List[str] = []
    status: TemplateStatus = TemplateStatus.DRAFT
    user_id: str
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Template name cannot be empty')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        # タグの重複削除と正規化
        return list(set(tag.strip().lower() for tag in v if tag.strip()))
    
    def extract_variables(self) -> List[str]:
        """コンテンツから変数を抽出"""
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, self.content)
        return list(set(matches))  # 重複削除
    
    def render(self, variables: Dict[str, Any]) -> str:
        """変数を使ってコンテンツをレンダリング"""
        rendered_content = self.content
        
        for var_name, value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            rendered_content = rendered_content.replace(placeholder, str(value))
        
        return rendered_content
    
    def validate_variables(self, variables: Dict[str, Any]) -> Dict[str, List[str]]:
        """変数バリデーション"""
        errors = {}
        
        for template_var in self.variables:
            var_name = template_var.name
            value = variables.get(var_name)
            
            if not template_var.validate_value(value):
                if var_name not in errors:
                    errors[var_name] = []
                
                if value is None and template_var.required:
                    errors[var_name].append(f"{var_name} is required")
                elif value is not None:
                    errors[var_name].append(f"Invalid value for {var_name}")
        
        return errors
    
    def is_valid(self) -> bool:
        """テンプレートの有効性チェック"""
        return bool(self.name and self.content and self.user_id)
    
    def increment_usage(self) -> None:
        """使用回数をインクリメント"""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()
    
    def update_content(self, content: str, variables: Optional[List[TemplateVariable]] = None) -> None:
        """コンテンツ更新"""
        self.content = content
        if variables is not None:
            self.variables = variables
        self.updated_at = datetime.utcnow()
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }