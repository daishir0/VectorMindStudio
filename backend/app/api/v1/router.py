from fastapi import APIRouter

from app.api.v1 import auth, templates, files, search, outputs, vectordb, chat

api_router = APIRouter()

# 認証関連のエンドポイント
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# テンプレート関連のエンドポイント
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])

# ファイル関連のエンドポイント
api_router.include_router(files.router, prefix="/files", tags=["files"])

# 検索関連のエンドポイント
api_router.include_router(search.router, prefix="/search", tags=["search"])

# アウトプット関連のエンドポイント
api_router.include_router(outputs.router, prefix="/outputs", tags=["outputs"])

# VectorDB関連のエンドポイント
api_router.include_router(vectordb.router, prefix="/vectordb", tags=["vectordb"])

# チャット関連のエンドポイント
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
