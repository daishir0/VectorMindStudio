import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { outputService } from '../services/outputService';
import { OutputDetailResponse } from '../types';
import toast from 'react-hot-toast';
import { ArrowLeft } from 'lucide-react';

const OutputDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [output, setOutput] = useState<OutputDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchOutput(id);
    }
  }, [id]);

  const fetchOutput = async (outputId: string) => {
    try {
      setLoading(true);
      const response = await outputService.getOutput(outputId);
      setOutput(response);
    } catch (error) {
      toast.error('アウトプット詳細の取得に失敗しました。');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">読み込み中...</div>;
  }

  if (!output) {
    return <div className="text-center py-12">アウトプットが見つかりません。</div>;
  }

  return (
    <div className="space-y-6">
        <div>
            <Link to="/outputs" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700">
                <ArrowLeft className="h-4 w-4 mr-2" />
                アウトプット一覧に戻る
            </Link>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
            <h1 className="text-2xl font-bold text-gray-900">アウトプット詳細: {output.id}</h1>
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm text-gray-600">
                <p><strong>テンプレートID:</strong> {output.template_id}</p>
                <p><strong>生成日時:</strong> {new Date(output.created_at).toLocaleString('ja-JP')}</p>
                <p><strong>AIモデル:</strong> {output.ai_model}</p>
                <p><strong>生成時間:</strong> {output.generation_time}ms</p>
            </div>
            <div className="mt-6">
                <h3 className="text-lg font-semibold text-gray-800">入力変数:</h3>
                <pre className="mt-2 p-4 bg-gray-100 rounded-md text-sm">{JSON.stringify(output.input_variables, null, 2)}</pre>
            </div>
            <div className="mt-6">
                <h3 className="text-lg font-semibold text-gray-800">生成コンテンツ:</h3>
                <div className="mt-2 p-4 border border-gray-200 rounded-md whitespace-pre-wrap">{output.generated_content}</div>
            </div>
        </div>
    </div>
  );
};

export default OutputDetailPage;
