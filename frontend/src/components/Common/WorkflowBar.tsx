import React from 'react';
import { LucideIcon, ArrowRight, ArrowRightLeft, Check } from 'lucide-react';

export interface WorkflowStep {
  number: number;
  icon: LucideIcon;
  label: string;
  description: string;
  status: 'pending' | 'current' | 'completed';
}

interface WorkflowBarProps {
  steps: WorkflowStep[];
  bidirectional?: boolean;
}

const WorkflowBar: React.FC<WorkflowBarProps> = ({ steps, bidirectional = false }) => {
  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-100">
      <p className="text-sm font-medium text-gray-700 mb-4">ワークフロー:</p>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <React.Fragment key={step.number}>
            {/* ステップカード */}
            <div className="flex flex-col items-center flex-1">
              <div
                className={`
                  relative rounded-lg p-4 transition-all duration-300 w-full max-w-[160px]
                  ${step.status === 'current'
                    ? 'bg-blue-600 text-white shadow-lg scale-105'
                    : step.status === 'completed'
                    ? 'bg-green-100 text-green-800 border-2 border-green-300'
                    : 'bg-white text-gray-600 border-2 border-gray-200'
                  }
                `}
              >
                {/* 完了チェックマーク */}
                {step.status === 'completed' && (
                  <div className="absolute -top-2 -right-2 bg-green-500 rounded-full p-1">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                )}

                {/* アイコンとラベル */}
                <div className="flex flex-col items-center space-y-2">
                  <step.icon className={`w-8 h-8 ${
                    step.status === 'current' ? 'animate-pulse' : ''
                  }`} />
                  <div className="text-center">
                    <div className={`text-xs font-semibold ${
                      step.status === 'current' ? 'text-white' : 'text-gray-500'
                    }`}>
                      {step.number}. {step.label}
                    </div>
                  </div>
                </div>
              </div>

              {/* ステータス説明 */}
              <div className="mt-2 text-center">
                <span className={`text-xs font-medium ${
                  step.status === 'completed' ? 'text-green-600' :
                  step.status === 'current' ? 'text-blue-600' :
                  'text-gray-500'
                }`}>
                  {step.status === 'completed' ? '✓' :
                   step.status === 'current' ? '■' :
                   '□'} {step.description}
                </span>
              </div>
            </div>

            {/* 矢印 */}
            {index < steps.length - 1 && (
              <div className="flex items-center px-2 text-gray-400">
                {bidirectional ? (
                  <ArrowRightLeft className="w-6 h-6" />
                ) : (
                  <ArrowRight className="w-6 h-6" />
                )}
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default WorkflowBar;
