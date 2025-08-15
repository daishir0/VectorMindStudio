# VectorMindStudio

## Overview
VectorMindStudio is a next-generation knowledge management and utilization platform that seamlessly integrates AI capabilities with human insights. Built with cutting-edge vector database technology and AI-powered content generation, it enables organizations to transform scattered information into actionable knowledge.

Key features:
- **AI-Powered Template Engine** - Create and execute intelligent content templates with context-aware AI generation
- **Advanced Vector Search** - Semantic similarity search using OpenAI embeddings and ChromaDB
- **Intelligent File Processing** - Automated document conversion and vectorization with support for multiple formats
- **Real-time Chat Interface** - Interactive AI assistant for knowledge exploration and content creation
- **Template Management System** - Design, organize, and reuse content templates for consistent output
- **Collaborative Knowledge Base** - Team-based knowledge sharing and collaborative content creation
- **RESTful API Architecture** - Full API access for integration with external systems

## Installation

### Prerequisites
- Python 3.11+ with conda environment
- Node.js 18+ and npm
- OpenAI API key
- Git

### Step-by-step Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/VectorMindStudio
   cd VectorMindStudio
   ```

2. **Set up Python environment**
   ```bash
   conda activate 311
   ```

3. **Configure backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env file with your OpenAI API key and other settings
   ```

4. **Configure frontend**
   ```bash
   cd frontend
   npm install
   ```

5. **Initialize database**
   ```bash
   cd backend
   alembic upgrade head
   ```

## Usage

### Quick Start with Management Script
```bash
# Start all services (recommended)
./vectormindstudio.sh start

# Check system status
./vectormindstudio.sh status

# Stop all services
./vectormindstudio.sh stop

# Restart services
./vectormindstudio.sh restart
```

### Manual Startup
**Start ChromaDB (Terminal 1)**
```bash
chroma run --host 0.0.0.0 --port 8011 --path ./chromadb_data
```

**Start Backend API (Terminal 2)**
```bash
cd backend
conda activate 311
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

**Start Frontend (Terminal 3)**
```bash
cd frontend
npm run dev
```

### Web Interface
After starting the system, access the web interface at:
- Frontend: http://localhost:3011
- Backend API: http://localhost:8010
- API Documentation: http://localhost:8010/docs
- ChromaDB: http://localhost:8011

### Core Features

#### 1. File Upload & Processing
- Upload documents in various formats (PDF, Word, Text, etc.)
- Automatic content extraction and vectorization
- Searchable knowledge base creation

#### 2. Template Management
- Create custom content templates
- AI-powered template execution with context awareness
- Template library for reusable content patterns

#### 3. Intelligent Chat
- Context-aware AI conversations
- Knowledge base integration for accurate responses
- Real-time interaction with uploaded content

#### 4. Vector Search
- Semantic similarity search across all content
- Advanced filtering and ranking capabilities
- Multi-modal search support

### API Endpoints
- `POST /api/v1/files/upload` - Upload and process files
- `GET /api/v1/files` - List uploaded files
- `POST /api/v1/templates` - Create content templates
- `POST /api/v1/templates/{id}/use` - Execute templates with AI
- `POST /api/v1/chat/message` - Interactive chat with AI
- `POST /api/v1/search` - Vector-based content search
- `GET /api/v1/outputs` - Retrieve generated content

## Project Structure

```
VectorMindStudio/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints
│   │   ├── core/              # Configuration & security
│   │   ├── domain/            # Business logic entities
│   │   ├── infrastructure/    # Data access & external services
│   │   ├── schemas/           # Pydantic models
│   │   └── services/          # Business logic services
│   ├── alembic/               # Database migrations
│   └── requirements.txt
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client services
│   │   └── types/            # TypeScript type definitions
│   └── package.json
├── chromadb_data/             # Vector database storage
├── logs/                      # System logs
└── vectormindstudio.sh        # System management script
```

## Technology Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Database**: SQLite (relational) + ChromaDB (vector)
- **AI/ML**: OpenAI GPT-4o-mini, text-embedding-3-small
- **File Processing**: markitdown for document conversion
- **Authentication**: JWT-based authentication system

## Notes
- Ensure your OpenAI API key is properly configured in the `.env` file
- The system automatically manages ChromaDB persistence across restarts
- All uploaded files are processed and stored in the `backend/app/storage/` directory
- Vector embeddings are cached for improved performance
- The system supports concurrent file processing with automatic error handling
- Comprehensive logging is available in the `logs/` directory for troubleshooting

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# VectorMindStudio

## 概要
VectorMindStudioは、AIと人間の知見を融合した次世代の知識管理・活用プラットフォームです。最新のベクターデータベース技術とAI駆動のコンテンツ生成機能を組み合わせ、散在する情報を実用的な知識に変換することを可能にします。

主な機能:
- **AI搭載テンプレートエンジン** - コンテキスト認識AI生成によるインテリジェントなコンテンツテンプレートの作成と実行
- **高度なベクター検索** - OpenAI埋め込みとChromaDBを使用したセマンティック類似性検索
- **インテリジェントファイル処理** - 複数フォーマット対応の自動文書変換・ベクトル化
- **リアルタイムチャットインターフェース** - 知識探索とコンテンツ作成のためのインタラクティブAIアシスタント
- **テンプレート管理システム** - 一貫した出力のためのコンテンツテンプレートの設計・整理・再利用
- **協働ナレッジベース** - チームベースの知識共有と協働コンテンツ作成
- **RESTful API アーキテクチャ** - 外部システム統合のための完全API アクセス

## インストール方法

### 前提条件
- Python 3.11+ （conda環境）
- Node.js 18+ と npm
- OpenAI APIキー
- Git

### Step by stepのインストール方法

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/yourusername/VectorMindStudio
   cd VectorMindStudio
   ```

2. **Python環境の設定**
   ```bash
   conda activate 311
   ```

3. **バックエンドの設定**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # .envファイルにOpenAI APIキーやその他の設定を記入
   ```

4. **フロントエンドの設定**
   ```bash
   cd frontend
   npm install
   ```

5. **データベースの初期化**
   ```bash
   cd backend
   alembic upgrade head
   ```

## 使い方

### 管理スクリプトによるクイックスタート
```bash
# 全サービスの開始（推奨）
./vectormindstudio.sh start

# システム状態の確認
./vectormindstudio.sh status

# 全サービスの停止
./vectormindstudio.sh stop

# サービスの再起動
./vectormindstudio.sh restart
```

### 手動起動
**ChromaDBの起動（ターミナル1）**
```bash
chroma run --host 0.0.0.0 --port 8011 --path ./chromadb_data
```

**バックエンドAPIの起動（ターミナル2）**
```bash
cd backend
conda activate 311
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

**フロントエンドの起動（ターミナル3）**
```bash
cd frontend
npm run dev
```

### Webインターフェース
システム起動後、以下のURLでアクセスできます：
- フロントエンド: http://localhost:3011
- バックエンドAPI: http://localhost:8010
- API文書: http://localhost:8010/docs
- ChromaDB: http://localhost:8011

### 主要機能

#### 1. ファイルアップロード・処理
- 各種フォーマット（PDF、Word、テキストなど）の文書アップロード
- 自動コンテンツ抽出とベクトル化
- 検索可能なナレッジベースの作成

#### 2. テンプレート管理
- カスタムコンテンツテンプレートの作成
- コンテキスト認識によるAI搭載テンプレート実行
- 再利用可能なコンテンツパターンのためのテンプレートライブラリ

#### 3. インテリジェントチャット
- コンテキスト認識AI会話
- 正確な回答のためのナレッジベース統合
- アップロードしたコンテンツとのリアルタイム対話

#### 4. ベクター検索
- 全コンテンツでのセマンティック類似性検索
- 高度なフィルタリングとランキング機能
- マルチモーダル検索サポート

### APIエンドポイント
- `POST /api/v1/files/upload` - ファイルのアップロードと処理
- `GET /api/v1/files` - アップロード済みファイルの一覧
- `POST /api/v1/templates` - コンテンツテンプレートの作成
- `POST /api/v1/templates/{id}/use` - AIによるテンプレート実行
- `POST /api/v1/chat/message` - AIとのインタラクティブチャット
- `POST /api/v1/search` - ベクターベースのコンテンツ検索
- `GET /api/v1/outputs` - 生成されたコンテンツの取得

## プロジェクト構造

```
VectorMindStudio/
├── backend/                    # FastAPI バックエンド
│   ├── app/
│   │   ├── api/v1/            # API エンドポイント
│   │   ├── core/              # 設定・セキュリティ
│   │   ├── domain/            # ビジネスロジックエンティティ
│   │   ├── infrastructure/    # データアクセス・外部サービス
│   │   ├── schemas/           # Pydantic モデル
│   │   └── services/          # ビジネスロジックサービス
│   ├── alembic/               # データベースマイグレーション
│   └── requirements.txt
├── frontend/                   # React フロントエンド
│   ├── src/
│   │   ├── components/        # 再利用可能なUIコンポーネント
│   │   ├── pages/            # ページコンポーネント
│   │   ├── services/         # APIクライアントサービス
│   │   └── types/            # TypeScript型定義
│   └── package.json
├── chromadb_data/             # ベクターデータベースストレージ
├── logs/                      # システムログ
└── vectormindstudio.sh        # システム管理スクリプト
```

## 技術スタック
- **バックエンド**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **フロントエンド**: React 18, TypeScript, Vite, Tailwind CSS
- **データベース**: SQLite（関係型） + ChromaDB（ベクター）
- **AI/ML**: OpenAI GPT-4o-mini, text-embedding-3-small
- **ファイル処理**: markitdown による文書変換
- **認証**: JWTベース認証システム

## 注意点
- `.env`ファイルにOpenAI APIキーが適切に設定されていることを確認してください
- システムは再起動時にChromaDBの永続化を自動管理します
- アップロードされたファイルは全て`backend/app/storage/`ディレクトリに処理・保存されます
- ベクター埋め込みはパフォーマンス向上のためキャッシュされます
- システムは自動エラーハンドリング付きの並行ファイル処理をサポートします
- トラブルシューティング用の包括的なログが`logs/`ディレクトリで利用可能です

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。