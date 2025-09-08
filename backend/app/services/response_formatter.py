"""
AIエージェント実行結果を適切なユーザーレスポンスにフォーマットするクラス
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """AIエージェント実行結果の統合・フォーマット"""
    
    @staticmethod
    def format_supervisor_response(
        intent_analysis: Dict[str, Any],
        workflow_plan: Dict[str, Any]
    ) -> str:
        """SupervisorAgentの結果をユーザー向けメッセージに変換"""
        intent_type = intent_analysis.get("intent_type", "unknown")
        confidence = intent_analysis.get("confidence", 0)
        
        if intent_type == "query_existing":
            target = intent_analysis.get("target_sections", ["セクション"])[0]
            return f"「{target}」に関する情報をお探しですね。既存の内容を検索します。"
        elif intent_type == "create_new":
            return "新しいコンテンツの作成をサポートします。"
        elif intent_type == "edit_existing":
            return "既存のコンテンツの編集をお手伝いします。"
        else:
            return f"ご依頼を分析しました（信頼度: {confidence:.0%}）。最適なアプローチで対応いたします。"

    @staticmethod
    def format_section_query_response(
        query_result: Dict[str, Any],
        original_query: str
    ) -> Dict[str, Any]:
        """SectionQueryAgentの結果を詳細な作業報告としてフォーマット"""
        execution_time = query_result.get("execution_time", "不明")
        sections_searched = query_result.get("sections_searched", 0)
        
        if not query_result.get("success", False):
            return {
                "message": f"✅ セクション検索タスクが完了しました\n\n🔍 実行内容:\n- 検索クエリ: 「{original_query}」\n- 対象セクション数: {sections_searched}件\n- 検索手法: ファジー文字列マッチング\n\n❌ 検索結果: 該当するセクションが見つかりませんでした\n\n💡 次のアクション提案:\n- 検索キーワードを変更してみる\n- 新しいセクションを作成する\n- 類似するセクション名を確認する",
                "found_content": False,
                "work_summary": {
                    "task_type": "section_search", 
                    "execution_time": execution_time,
                    "sections_searched": sections_searched,
                    "matches_found": 0
                }
            }
        
        found_sections = query_result.get("found_sections", [])
        if not found_sections:
            return {
                "message": f"✅ セクション検索タスクが完了しました\n\n🔍 実行内容:\n- 検索クエリ: 「{original_query}」\n- 検索結果: 0件\n\n💡 関連セクションをお探しの場合は、キーワードを変更してお試しください。",
                "found_content": False
            }
        
        # 最も関連性の高いセクション
        best_match = max(found_sections, key=lambda x: x.get("similarity_score", 0))
        section_title = best_match.get("title", "不明")
        section_content = best_match.get("content", "内容が取得できませんでした")
        word_count = best_match.get("word_count", 0)
        similarity_score = best_match.get("similarity_score", 0)
        updated_at = best_match.get("updated_at", "不明")
        
        # 作業完了報告メッセージ
        message = f"""✅ セクション検索タスクが完了しました！

🔍 実行内容:
- 検索クエリ: 「{original_query}」
- 対象セクション数: {sections_searched}件
- マッチング手法: ファジー文字列マッチング
- 実行時間: {execution_time}

📊 検索結果:
- 発見セクション数: {len(found_sections)}件
- 最高類似度: {similarity_score:.0%} {'(完全一致)' if similarity_score >= 1.0 else ''}
- セクション名: "{section_title}"
- コンテンツ: {word_count}語
- 最終更新: {updated_at}

📖 以下が取得した{section_title}セクションの内容です:

{section_content}"""
        
        if word_count > 0:
            message += f"\n\n({word_count}語)"
            
        return {
            "message": message,
            "found_content": True,
            "primary_section": {
                "id": best_match.get("id"),
                "title": section_title,
                "content": section_content,
                "word_count": word_count,
                "similarity_score": similarity_score
            },
            "work_summary": {
                "task_type": "section_search",
                "execution_time": execution_time,
                "sections_searched": sections_searched,
                "matches_found": len(found_sections),
                "best_match_score": similarity_score,
                "method_used": "fuzzy_string_matching"
            },
            "additional_matches": len(found_sections) - 1
        }

    @staticmethod
    def format_writer_response(writer_result: Dict[str, Any]) -> Dict[str, Any]:
        """WriterAgentの結果を詳細な作業報告としてフォーマット"""
        if not writer_result.get("success", False):
            error_msg = writer_result.get("error_message", "不明なエラー")
            return {
                "message": f"❌ コンテンツ生成タスクでエラーが発生しました\n\n🔍 実行内容:\n- タスク: コンテンツ生成\n- エラー詳細: {error_msg}\n\n💡 次のアクション提案:\n- パラメータを調整して再実行\n- 異なるアプローチで生成を試行",
                "generated_content": False,
                "work_summary": {
                    "task_type": "content_generation",
                    "success": False,
                    "error": error_msg
                }
            }
        
        content = writer_result.get("generated_content", "")
        word_count = writer_result.get("word_count", len(content.split()) if content else 0)
        section_title = writer_result.get("target_section", "新規セクション")
        execution_time = writer_result.get("execution_time", "不明")
        writing_style = writer_result.get("style", "academic")
        quality_metrics = writer_result.get("quality_metrics", {})
        
        # 品質指標の表示
        quality_info = ""
        if quality_metrics:
            readability = quality_metrics.get("readability_score", "N/A")
            academic_tone = quality_metrics.get("academic_tone", "不明")
            coherence = quality_metrics.get("coherence", "不明")
            quality_info = f"""
📊 品質指標:
- 可読性スコア: {readability}/10
- 学術的トーン: {academic_tone}
- 文章の一貫性: {coherence}"""
        
        message = f"""✅ コンテンツ生成タスクが完了しました！

🖊️ 実行内容:
- 対象セクション: {section_title}
- 生成モード: 新規作成
- 文章スタイル: {writing_style}
- 実行時間: {execution_time}

📝 生成結果:
- 生成語数: {word_count}語
- コンテンツ品質: 良好{quality_info}

📖 以下が生成した{section_title}セクションのコンテンツです:

{content}"""
        
        return {
            "message": message,
            "generated_content": True,
            "content_info": {
                "section": section_title,
                "word_count": word_count,
                "writing_style": writing_style,
                "execution_time": execution_time
            },
            "work_summary": {
                "task_type": "content_generation",
                "target_section": section_title,
                "word_count": word_count,
                "execution_time": execution_time,
                "quality_metrics": quality_metrics,
                "success": True
            }
        }

    @staticmethod
    def format_outline_response(outline_result: Dict[str, Any]) -> Dict[str, Any]:
        """OutlineAgentの結果をフォーマット"""
        if not outline_result.get("success", False):
            return {
                "message": "アウトライン操作中にエラーが発生しました。"
            }
        
        action = outline_result.get("action", "unknown")
        outline_structure = outline_result.get("outline_structure", [])
        
        if action == "create_section":
            new_section = outline_result.get("created_section", {})
            return {
                "message": f"新しいセクション「{new_section.get('title', '無題')}」を作成しました。",
                "created_section": new_section
            }
        elif action == "reorder":
            return {
                "message": f"セクションの順序を更新しました。現在{len(outline_structure)}個のセクションがあります。",
                "outline_structure": outline_structure
            }
        else:
            return {
                "message": f"アウトライン操作が完了しました。",
                "outline_structure": outline_structure
            }

    @staticmethod
    def format_summary_response(summary_result: Dict[str, Any]) -> Dict[str, Any]:
        """SummaryAgentの結果をフォーマット"""
        if not summary_result.get("success", False):
            return {"message": "要約の生成中にエラーが発生しました。"}
        
        summary_text = summary_result.get("summary", "")
        word_count = summary_result.get("word_count", len(summary_text.split()))
        key_points = summary_result.get("key_points", [])
        
        message = f"論文の要約を作成しました（{word_count}語）：\n\n{summary_text}"
        if key_points:
            message += "\n\n**主要ポイント：**\n"
            for i, point in enumerate(key_points, 1):
                message += f"{i}. {point}\n"
        
        return {
            "message": message,
            "summary_info": {
                "word_count": word_count,
                "key_points": key_points
            }
        }

    @staticmethod
    def format_logic_validator_response(validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """LogicValidatorAgentの結果をフォーマット"""
        if not validation_result.get("success", False):
            return {"message": "論理検証中にエラーが発生しました。"}
        
        issues = validation_result.get("identified_issues", [])
        overall_score = validation_result.get("coherence_score", 0)
        
        if not issues:
            return {
                "message": f"論理検証が完了しました。論文の一貫性は良好です（スコア: {overall_score:.1f}/10）。",
                "validation_passed": True
            }
        
        message = f"論理検証が完了しました。{len(issues)}件の改善提案があります：\n\n"
        for i, issue in enumerate(issues, 1):
            severity = issue.get("severity", "中")
            section = issue.get("section", "不明")
            suggestion = issue.get("suggestion", "詳細な提案はありません")
            message += f"{i}. **{section}** ({severity}): {suggestion}\n"
        
        return {
            "message": message,
            "validation_issues": issues,
            "overall_score": overall_score
        }

    @classmethod
    def integrate_all_results(
        cls,
        intent_analysis: Dict[str, Any],
        task_results: Dict[str, Any],
        original_query: str
    ) -> Dict[str, Any]:
        """全てのエージェント実行結果を統合"""
        final_message_parts = []
        references = []
        task_summaries = {}
        
        # 各エージェントの結果を処理
        for agent_name, result in task_results.items():
            if not isinstance(result, dict):
                continue
                
            if agent_name == "SectionQueryAgent":
                formatted = cls.format_section_query_response(result, original_query)
                final_message_parts.append(formatted["message"])
                if formatted.get("found_content") and formatted.get("primary_section"):
                    references.append({
                        "section_id": formatted["primary_section"]["id"],
                        "title": formatted["primary_section"]["title"],
                        "content": formatted["primary_section"]["content"]
                    })
                task_summaries["section_query"] = "完了"
                
            elif agent_name == "WriterAgent":
                formatted = cls.format_writer_response(result)
                final_message_parts.append(formatted["message"])
                task_summaries["content_generation"] = "完了"
                
            elif agent_name == "OutlineAgent":
                formatted = cls.format_outline_response(result)
                final_message_parts.append(formatted["message"])
                task_summaries["outline_management"] = "完了"
                
            elif agent_name == "SummaryAgent":
                formatted = cls.format_summary_response(result)
                final_message_parts.append(formatted["message"])
                task_summaries["summarization"] = "完了"
                
            elif agent_name == "LogicValidatorAgent":
                formatted = cls.format_logic_validator_response(result)
                final_message_parts.append(formatted["message"])
                task_summaries["validation"] = "完了"
                
            elif agent_name == "AnalysisAgent":
                # 分析結果の処理
                if result.get("success", False):
                    response = "論文の構造分析結果をお答えします。\n\n"
                    
                    # 全体評価
                    if "overall_assessment" in result:
                        assessment = result["overall_assessment"]
                        response += f"【全体評価】\n{assessment}\n\n"
                    
                    # 平均スコア
                    if "average_critical_score" in result:
                        score = result["average_critical_score"]
                        response += f"【批判的評価スコア】\n{score:.1f}/10\n\n"
                    
                    # 批判的問題点
                    critical_issues = result.get("critical_issues", [])
                    if critical_issues:
                        response += "【発見された問題点】\n"
                        for i, issue in enumerate(critical_issues[:5], 1):
                            response += f"{i}. {issue}\n"
                        response += "\n"
                    
                    # 改善提案
                    suggestions = result.get("improvement_suggestions", [])
                    if suggestions:
                        response += "【改善提案】\n"
                        for i, suggestion in enumerate(suggestions[:5], 1):
                            response += f"{i}. {suggestion}\n"
                        response += "\n"
                    
                    # セクション別分析結果
                    analysis_results = result.get("analysis_results", [])
                    if analysis_results:
                        response += f"【分析対象】\n{len(analysis_results)}個のセクションを分析しました。\n"
                        for analysis in analysis_results[:3]:
                            section_title = analysis.get("section_title", "不明")
                            score = analysis.get("critical_score", 0)
                            response += f"・{section_title}: {score}/10\n"
                    
                    final_message_parts.append(response)
                    task_summaries["analysis"] = "完了"
                    
            elif agent_name == "QualityAgent":
                # 品質評価結果の処理
                if result.get("success", False):
                    response = "論文の品質評価結果をお答えします。\n\n"
                    
                    # 総合品質スコア
                    if "overall_quality" in result:
                        score = result["overall_quality"]
                        response += f"【総合品質スコア】\n{score:.1f}/10\n\n"
                    
                    # 出版準備度
                    if "readiness_assessment" in result:
                        readiness = result["readiness_assessment"]
                        response += f"【出版準備度】\n{readiness}\n\n"
                    
                    # 改善推奨事項
                    recommendations = result.get("improvement_recommendations", [])
                    if recommendations:
                        response += "【改善推奨事項】\n"
                        for i, rec in enumerate(recommendations[:5], 1):
                            response += f"{i}. {rec}\n"
                        response += "\n"
                    
                    # セクション別品質スコア
                    quality_scores = result.get("quality_scores", {})
                    if quality_scores:
                        response += "【セクション別品質】\n"
                        for section, score in list(quality_scores.items())[:3]:
                            response += f"・{section}: {score:.1f}/10\n"
                    
                    final_message_parts.append(response)
                    task_summaries["quality"] = "完了"
        
        # 最終メッセージの組み立て
        if not final_message_parts:
            final_message = "処理を実行しましたが、結果を取得できませんでした。"
        elif len(final_message_parts) == 1:
            final_message = final_message_parts[0]
        else:
            final_message = "\n\n---\n\n".join(final_message_parts)
        
        # 提案生成
        suggestions = cls._generate_context_suggestions(
            intent_analysis, task_results, references
        )
        
        return {
            "message": final_message,
            "todo_tasks": [],
            "task_results": task_summaries,
            "references": references,
            "suggestions": suggestions,
            "success": True
        }
    
    @staticmethod
    def _generate_context_suggestions(
        intent_analysis: Dict[str, Any],
        task_results: Dict[str, Any], 
        references: List[Dict[str, Any]]
    ) -> List[str]:
        """コンテキストに応じた提案を生成"""
        suggestions = []
        
        # セクション検索が成功した場合
        if any("SectionQueryAgent" in name for name in task_results.keys()):
            if references:
                ref_title = references[0].get("title", "セクション")
                suggestions.extend([
                    f"{ref_title}セクションを編集しますか？",
                    "関連する他のセクションも確認しますか？",
                    "このセクションの要約を作成しますか？"
                ])
        
        # コンテンツ生成が実行された場合  
        if any("WriterAgent" in name for name in task_results.keys()):
            suggestions.extend([
                "生成されたコンテンツを校正しますか？",
                "論理構造を検証しますか？",
                "他のセクションも生成しますか？"
            ])
        
        # デフォルト提案
        if not suggestions:
            suggestions = [
                "論文の進捗を確認しますか？",
                "新しいセクションを作成しますか？",
                "論文全体をエクスポートしますか？"
            ]
        
        return suggestions[:3]  # 最大3つまで