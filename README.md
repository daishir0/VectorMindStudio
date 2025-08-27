# VectorMindStudio

## Overview
VectorMindStudio is a next-generation knowledge management and utilization platform that seamlessly integrates AI capabilities with human insights. Built with cutting-edge vector database technology and AI-powered content generation, it enables organizations to transform scattered information into actionable knowledge.

Key features:
- **AI-Powered Research Paper Writing** - Complete academic paper composition system with IMRAD structure support and multi-agent AI collaboration
- **Multi-Agent AI System** - 5 specialized AI agents (Outline, Summary, Writer, LogicValidator, Reference) working in coordination for high-quality research output
- **Research Discussion Interface** - Interactive chat sessions with AI research assistants for collaborative paper development and academic consultation
- **AI-Powered Template Engine** - Create and execute intelligent content templates with context-aware AI generation
- **Advanced Vector Search** - Semantic similarity search using OpenAI embeddings and ChromaDB
- **Tag-Based Filtering System** - Advanced tag management for precise content filtering across search, chat, and template execution
- **Intelligent File Processing** - Automated document conversion and vectorization with support for multiple formats
- **Real-time Chat Interface** - Interactive AI assistant for knowledge exploration and content creation with tag-filtered RAG
- **Template Management System** - Design, organize, and reuse content templates for consistent output
- **Collaborative Knowledge Base** - Team-based knowledge sharing and collaborative content creation
- **RESTful API Architecture** - Full API access for integration with external systems

## Installation

### Prerequisites
- Python 3.11+
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
   # Create and activate a Python virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Configure backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env file with your OpenAI API key and other settings
   # IMPORTANT: Generate a secure SECRET_KEY for JWT tokens
   python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
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

### Starting the System
**Start ChromaDB (Terminal 1)**
```bash
chroma run --host 0.0.0.0 --port 8011 --path ./chromadb_data
```

**Start Backend API (Terminal 2)**
```bash
cd backend
# Activate your Python environment if using virtual environment
# source venv/bin/activate  # On Windows: venv\Scripts\activate
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

#### Demo Account
For new users, the system provides a simple demo account for immediate access:
- **Username**: `demo`
- **Password**: `demo`
- **Features**: Fixed demo credentials for easy testing and evaluation
- **Production**: Demo account feature is automatically disabled in production environments

### Core Features

#### 1. Research Paper Writing System
- **Academic Paper Composition** - Complete IMRAD (Introduction, Methods, Results, Analysis, Discussion) structure support
- **Multi-Agent AI Collaboration** - 5 specialized AI agents working together:
  - **OutlineAgent** - Hierarchical paper structure management and section organization
  - **SummaryAgent** - Content summarization and abstract generation
  - **WriterAgent** - High-quality academic content generation and writing assistance
  - **LogicValidatorAgent** - Logical consistency verification and argument validation
  - **ReferenceAgent** - Citation management and reference formatting (IEEE style)
- **Research Discussion Sessions** - Interactive chat with AI research assistants for:
  - Paper structure consultation and improvement
  - Research methodology guidance
  - Literature review assistance
  - Argument validation and enhancement
- **Hierarchical Section Management** - Automated section numbering and structural organization
- **Real-time Collaboration** - Live editing and AI-assisted writing workflow

#### 2. File Upload & Processing
- Upload documents in various formats (PDF, Word, Text, etc.)
- Automatic content extraction and vectorization
- Tag assignment and management for uploaded files
- Searchable knowledge base creation

#### 3. Advanced Tag-Based Filtering
- **Smart Tag Management** - Assign multiple tags to uploaded files for precise categorization
- **Cross-Platform Filtering** - Use tags to filter content across search, chat, and template execution
- **Dynamic Tag Selection** - Real-time tag-based content filtering with visual tag selection interface
- **Computational Efficiency** - Reduce vector search computation by pre-filtering documents with tags

#### 4. Template Management
- Create custom content templates
- AI-powered template execution with context awareness and tag filtering
- Template library for reusable content patterns
- Tag-filtered context retrieval for more relevant AI generation

#### 5. Intelligent Chat
- Context-aware AI conversations with tag-filtered RAG (Retrieval-Augmented Generation)
- Knowledge base integration for accurate responses
- Real-time interaction with uploaded content using tag-based document filtering
- Precise AI responses based on selected document categories

#### 6. Vector Search
- Semantic similarity search across all content
- Tag-based pre-filtering for enhanced search precision
- Advanced filtering and ranking capabilities
- Multi-modal search support with tag categorization

### API Endpoints

#### Research Paper APIs
- `POST /api/v1/papers` - Create new research papers
- `GET /api/v1/papers` - List research papers with filtering
- `GET /api/v1/papers/{id}` - Retrieve paper details
- `PUT /api/v1/papers/{id}` - Update paper information
- `DELETE /api/v1/papers/{id}` - Delete research papers
- `GET /api/v1/papers/{id}/sections` - List paper sections
- `POST /api/v1/papers/{id}/sections` - Create new sections
- `POST /api/v1/papers/{id}/chat` - Create research discussion sessions
- `POST /api/v1/papers/{id}/chat/{session_id}/messages` - Send messages to AI research assistants

#### Core APIs  
- `POST /api/v1/files/upload` - Upload and process files
- `GET /api/v1/files` - List uploaded files with tag filtering support
- `GET /api/v1/files/tags/all` - Retrieve all available tags for filtering
- `PATCH /api/v1/files/{id}/tags` - Update file tags
- `POST /api/v1/templates` - Create content templates
- `POST /api/v1/templates/{id}/use` - Execute templates with AI and tag filtering
- `POST /api/v1/chat/message` - Interactive chat with AI and tag-based RAG
- `POST /api/v1/search` - Vector-based content search with tag filtering
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
├── chromadb_data/             # Vector database storage (created at runtime)
└── logs/                      # System logs (created at runtime)
```

## Technology Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Database**: SQLite (relational) + ChromaDB (vector)
- **AI/ML**: OpenAI GPT-4o-mini, text-embedding-3-small
- **File Processing**: markitdown for document conversion
- **Authentication**: JWT-based authentication system

## Notes
- **SECURITY**: Ensure your SECRET_KEY is properly configured in the `.env` file with a strong random value (32+ characters)
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
- **AI論文執筆システム** - IMRAD構成サポートとマルチエージェントAI連携による完全学術論文作成システム
- **マルチエージェントAIシステム** - 高品質研究成果のために連携する5つの専門AIエージェント（アウトライン・要約・執筆・論理検証・参考文献）
- **研究ディスカッションインターフェース** - 協働論文開発と学術相談のためのAI研究アシスタントとのインタラクティブチャットセッション
- **AI搭載テンプレートエンジン** - コンテキスト認識AI生成によるインテリジェントなコンテンツテンプレートの作成と実行
- **高度なベクター検索** - OpenAI埋め込みとChromaDBを使用したセマンティック類似性検索
- **タグベースフィルタリングシステム** - 検索、チャット、テンプレート実行全体での精密なコンテンツフィルタリングのための高度なタグ管理
- **インテリジェントファイル処理** - 複数フォーマット対応の自動文書変換・ベクトル化
- **リアルタイムチャットインターフェース** - タグフィルタ付きRAGによる知識探索とコンテンツ作成のためのインタラクティブAIアシスタント
- **テンプレート管理システム** - 一貫した出力のためのコンテンツテンプレートの設計・整理・再利用
- **協働ナレッジベース** - チームベースの知識共有と協働コンテンツ作成
- **RESTful API アーキテクチャ** - 外部システム統合のための完全API アクセス

## インストール方法

### 前提条件
- Python 3.11+
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
   # Python仮想環境の作成・有効化（推奨）
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
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

### システムの起動
**ChromaDBの起動（ターミナル1）**
```bash
chroma run --host 0.0.0.0 --port 8011 --path ./chromadb_data
```

**バックエンドAPIの起動（ターミナル2）**
```bash
cd backend
# Python仮想環境を有効化している場合
# source venv/bin/activate  # Windows: venv\Scripts\activate
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

#### デモアカウント
新規ユーザーの方へ、すぐにアクセスできる簡単なデモアカウントを提供しています：
- **ユーザー名**: `demo`
- **パスワード**: `demo`
- **特徴**: 簡単なテスト・評価用の固定認証情報
- **本番環境**: 本番環境ではデモアカウント機能は自動的に無効化されます

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
├── chromadb_data/             # ベクターデータベースストレージ（実行時作成）
└── logs/                      # システムログ（実行時作成）
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