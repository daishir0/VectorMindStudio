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
        
        content = writer_result.get("generated_content") or writer_result.get("draft_content") or writer_result.get("content", "")
        word_count = writer_result.get("word_count", len(content.split()) if content else 0)
        section_title = writer_result.get("target_section") or writer_result.get("section_title", "新規セクション")
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
        # カスタムメッセージがある場合はそれを優先
        custom_message = summary_result.get("custom_message")
        if custom_message:
            return {
                "message": custom_message,
                "summary_info": {
                    "custom_guidance": True
                }
            }

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
        logger.info(f"[ResponseFormatter] Processing {len(task_results)} agent results: {list(task_results.keys())}")
        for agent_name, result in task_results.items():
            logger.info(f"[ResponseFormatter] Processing agent: {agent_name}, result type: {type(result)}, has 'success': {result.get('success') if isinstance(result, dict) else 'N/A'}")
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
                logger.info(f"[ResponseFormatter] WriterAgent block entered")
                formatted = cls.format_writer_response(result)
                logger.info(f"[ResponseFormatter] WriterAgent formatted message length: {len(formatted['message'])}")
                final_message_parts.append(formatted["message"])
                logger.info(f"[ResponseFormatter] WriterAgent message appended. Current parts count: {len(final_message_parts)}")
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

            elif agent_name == "GenerationAgent":
                # コンテンツ生成結果の処理
                if result.get("success", False):
                    task_type = result.get("task_type", "generation")

                    if task_type == "outline_generation":
                        # アウトライン生成結果
                        response = "論文アウトラインの生成が完了しました。\n\n"

                        # outline_resultから情報を取得
                        outline_result = result.get("outline_result", result.get("generated_result", {}))

                        # 論文構造情報
                        paper_structure = outline_result.get("paper_structure", {})
                        if paper_structure:
                            # タイトル
                            title = paper_structure.get("title", "")
                            if title:
                                response += f"【提案タイトル】\n{title}\n\n"

                            # メインセクション
                            main_sections = paper_structure.get("main_sections", [])
                            if main_sections:
                                response += "【論文構成】\n"
                                for i, section in enumerate(main_sections, 1):
                                    section_title = section.get("title", f"セクション{i}")
                                    purpose = section.get("purpose", "")
                                    response += f"{i}. {section_title}"
                                    if purpose:
                                        response += f" - {purpose}"
                                    response += "\n"
                                response += "\n"

                        # 構造の合理性
                        structural_rationale = outline_result.get("structural_rationale", {})
                        if structural_rationale:
                            org_logic = structural_rationale.get("organization_logic", "")
                            if org_logic:
                                response += f"【構造化の論理】\n{org_logic}\n\n"

                        # 内容分配
                        content_distribution = outline_result.get("content_distribution", {})
                        if content_distribution:
                            total_length = content_distribution.get("total_estimated_length", "不明")
                            response += f"【推定総文字数】\n{total_length}\n\n"

                        # 完成度スコア
                        completeness = result.get("outline_completeness", outline_result.get("outline_completeness", 0))
                        if completeness > 0:
                            response += f"【アウトライン完成度】\n{completeness:.1%}\n"

                        final_message_parts.append(response)
                        task_summaries["outline_generation"] = "完了"

                    elif task_type == "section_generation":
                        # セクション生成結果
                        response = "セクションコンテンツの生成が完了しました。\n\n"

                        generated_result = result.get("generated_result", {})
                        generated_content = generated_result.get("generated_content", "")

                        if generated_content:
                            word_count = result.get("actual_word_count", 0)
                            response += f"【生成されたコンテンツ】\n（{word_count}文字）\n\n"

                            # コンテンツが長い場合は冒頭部分のみ表示
                            if len(generated_content) > 500:
                                response += generated_content[:500] + "...\n\n（全文は論文に保存されました）"
                            else:
                                response += generated_content

                        # 品質スコア
                        quality_score = result.get("quality_score", 0)
                        if quality_score > 0:
                            response += f"\n\n【品質スコア】\n{quality_score:.1%}"

                        final_message_parts.append(response)
                        task_summaries["section_generation"] = "完了"

                    elif task_type == "content_expansion":
                        # コンテンツ拡張結果
                        response = "既存コンテンツの拡張が完了しました。\n\n"

                        expansion_result = result.get("expansion_result", {})
                        expanded_content = expansion_result.get("expanded_content", "")

                        if expanded_content:
                            expansion_analysis = expansion_result.get("expansion_analysis", {})
                            expansion_ratio = expansion_analysis.get("expansion_ratio", result.get("actual_expansion_ratio", 1.0))
                            response += f"【拡張倍率】\n{expansion_ratio:.1f}倍\n\n"

                            # 拡張内容
                            if len(expanded_content) > 500:
                                response += f"【拡張後内容（冒頭部分）】\n{expanded_content[:500]}...\n"
                            else:
                                response += f"【拡張後内容】\n{expanded_content}\n"

                        final_message_parts.append(response)
                        task_summaries["content_expansion"] = "完了"

                    else:
                        # その他の生成タスク
                        response = f"コンテンツ生成（{task_type}）が完了しました。\n"
                        final_message_parts.append(response)
                        task_summaries["generation"] = "完了"

            elif agent_name == "StructureAgent":
                # 構造最適化結果の処理
                if result.get("success", False):
                    # actionまたはtask_typeフィールドでタスクタイプを判定
                    task_type = result.get("task_type") or result.get("action", "structure")

                    if task_type == "analyze_structure":
                        # 構造分析結果
                        response = "論文構造の分析が完了しました。\n\n"

                        # analysisオブジェクトから情報を取得
                        analysis = result.get("analysis", {})
                        structure_type = analysis.get("structure_type", result.get("structure_type", "不明"))
                        coherence_score = analysis.get("coherence_score", result.get("coherence_score", 0))

                        response += f"【現在の構造形式】\n{structure_type}\n\n"

                        # coherence_scoreは0.0-1.0の範囲なので10倍して表示
                        if coherence_score <= 1.0:
                            coherence_score = coherence_score * 10

                        response += f"【構造一貫性スコア】\n{coherence_score:.1f}/10\n\n"

                        # 問題点
                        issues = analysis.get("issues", result.get("issues", []))
                        if issues:
                            response += "【発見された問題点】\n"
                            for i, issue in enumerate(issues[:5], 1):
                                response += f"{i}. {issue}\n"
                            response += "\n"

                        # 強み
                        strengths = analysis.get("strengths", result.get("strengths", []))
                        if strengths:
                            response += "【構造の強み】\n"
                            for i, strength in enumerate(strengths[:3], 1):
                                response += f"{i}. {strength}\n"
                            response += "\n"

                        # 改善提案
                        suggestions = analysis.get("suggestions", result.get("suggestions", []))
                        if suggestions:
                            response += "【改善提案】\n"
                            for i, suggestion in enumerate(suggestions[:3], 1):
                                response += f"{i}. {suggestion}\n"

                        final_message_parts.append(response)
                        task_summaries["structure_analysis"] = "完了"

                    elif task_type == "suggest_restructure":
                        # 構造改善提案結果
                        response = "論文構造の改善提案が完了しました。\n\n"

                        # suggestionオブジェクトから情報を取得
                        suggestion = result.get("suggestion", {})
                        target_format = suggestion.get("target_format", result.get("target_format", "不明"))
                        rationale = suggestion.get("rationale", result.get("rationale", ""))

                        response += f"【推奨構造形式】\n{target_format}\n\n"

                        if rationale:
                            response += f"【推奨理由】\n{rationale}\n\n"

                        # アクションプラン
                        actions = suggestion.get("actions", result.get("actions", []))
                        if actions:
                            response += "【実行アクション】\n"
                            for i, action in enumerate(actions, 1):
                                action_type = action.get("action_type", action.get("type", "不明"))
                                details = action.get("details", action.get("description", ""))
                                response += f"{i}. {action_type}: {details}\n"
                            response += "\n"

                        # 期待される効果
                        benefits = suggestion.get("expected_benefits", result.get("expected_benefits", []))
                        if benefits:
                            response += "【期待される効果】\n"
                            for i, benefit in enumerate(benefits[:3], 1):
                                response += f"{i}. {benefit}\n"

                        final_message_parts.append(response)
                        task_summaries["structure_optimization"] = "完了"

                    elif task_type == "split_section":
                        # セクション分割結果
                        response = "✅ セクション分割タスクが完了しました！\n\n"

                        original_section_id = result.get("original_section_id", "")
                        new_sections = result.get("new_sections", [])
                        split_count = result.get("split_count", len(new_sections))

                        response += f"📐 実行内容:\n"
                        response += f"- 分割数: {split_count}個\n"
                        response += f"- 元セクションID: {original_section_id[:8]}...\n\n"

                        response += f"📝 新しいセクション:\n"
                        for idx, section in enumerate(new_sections, 1):
                            title = section.get("title", "不明")
                            word_count = section.get("word_count", 0)
                            response += f"{idx}. {title} ({word_count}語)\n"

                        final_message_parts.append(response)
                        task_summaries["structure_split"] = "完了"

                    elif task_type == "merge_sections":
                        # セクション統合結果
                        response = "✅ セクション統合タスクが完了しました！\n\n"

                        merged_section = result.get("merged_section", {})
                        deleted_ids = result.get("deleted_section_ids", [])

                        response += f"📐 実行内容:\n"
                        response += f"- 統合後タイトル: {merged_section.get('title', '不明')}\n"
                        response += f"- 統合後語数: {merged_section.get('word_count', 0)}語\n"
                        response += f"- 削除セクション数: {len(deleted_ids)}個\n"

                        final_message_parts.append(response)
                        task_summaries["structure_merge"] = "完了"

                    elif task_type == "restructure_with_content":
                        # 包括的再構成結果
                        response = "✅ 論文構造の包括的再構成が完了しました！\n\n"

                        target_format = result.get("target_format", "不明")
                        operations_count = result.get("operations_count", 0)
                        execution_results = result.get("execution_results", [])
                        restructure_plan = result.get("restructure_plan", {})

                        response += f"📐 実行内容:\n"
                        response += f"- 目標フォーマット: {target_format}\n"
                        response += f"- 実行操作数: {operations_count}個\n\n"

                        if execution_results:
                            response += f"🔧 実行した操作:\n"
                            op_types = {}
                            for result_item in execution_results:
                                op_type = result_item.get("type", "unknown")
                                op_types[op_type] = op_types.get(op_type, 0) + 1

                            for op_type, count in op_types.items():
                                type_names = {
                                    "split": "セクション分割",
                                    "merge": "セクション統合",
                                    "rename": "タイトル変更",
                                    "reorder": "セクション並び替え"
                                }
                                type_name = type_names.get(op_type, op_type)
                                response += f"- {type_name}: {count}回\n"

                        # 計画の理由
                        rationale = restructure_plan.get("rationale", "")
                        if rationale:
                            response += f"\n📝 再構成の理由:\n{rationale[:200]}"
                            if len(rationale) > 200:
                                response += "..."

                        final_message_parts.append(response)
                        task_summaries["structure_restructure"] = "完了"

                    else:
                        # その他の構造タスク
                        response = f"論文構造の{task_type}が完了しました。\n"
                        final_message_parts.append(response)
                        task_summaries["structure"] = "完了"

            elif agent_name == "EditingAgent":
                # コンテンツ編集・加筆結果の処理
                logger.info(f"[ResponseFormatter] EditingAgent block reached. result.get('success'): {result.get('success')}, type: {type(result.get('success'))}")
                if result.get("success", False):
                    logger.info(f"[ResponseFormatter] EditingAgent success condition passed")
                    response = "✅ コンテンツ編集タスクが完了しました！\n\n"

                    # 編集結果の取得
                    enhancement_results = result.get("enhancement_results", [])
                    sections_enhanced = result.get("sections_enhanced", len(enhancement_results))
                    total_content_added = result.get("total_content_added", 0)
                    enhancement_type = result.get("enhancement_type", "comprehensive")

                    response += f"🖊️ 実行内容:\n"
                    response += f"- 編集タイプ: {enhancement_type}\n"
                    response += f"- 編集セクション数: {sections_enhanced}個\n"
                    response += f"- 追加文字数: {total_content_added}文字\n\n"

                    # セクション別の編集結果
                    if enhancement_results:
                        response += "📝 編集結果:\n"
                        for idx, enhancement in enumerate(enhancement_results[:3], 1):
                            section_title = enhancement.get("section_title", "不明")
                            completeness_score = enhancement.get("completeness_score", 0)
                            enhancement_quality = enhancement.get("enhancement_quality", "moderate")

                            response += f"{idx}. {section_title}\n"
                            response += f"   - 品質: {enhancement_quality}\n"
                            response += f"   - 完成度: {completeness_score}/10\n"

                            # 追加された要素
                            added_elements = enhancement.get("added_elements", [])
                            if added_elements:
                                response += f"   - 追加内容: {', '.join(added_elements[:3])}\n"
                            response += "\n"

                        # 編集後のコンテンツ表示（最初のセクションのみ）
                        first_enhancement = enhancement_results[0]
                        enhanced_content = first_enhancement.get("enhanced_content", "")

                        # enhanced_contentがJSON文字列の場合はパース
                        if isinstance(enhanced_content, str) and enhanced_content.startswith("{"):
                            try:
                                import json
                                enhanced_data = json.loads(enhanced_content)
                                enhanced_content = enhanced_data.get("enhanced_content", "")
                            except:
                                pass

                        if enhanced_content and len(enhanced_content) > 100:
                            response += "📖 編集後のコンテンツ（冒頭部分）:\n\n"
                            response += enhanced_content[:500] + "...\n\n"
                            response += "（全文は論文に保存されました）"
                    else:
                        response += "編集が正常に完了しました。"

                    final_message_parts.append(response)
                    task_summaries["editing"] = "完了"

            elif agent_name == "DiscoveryAgent":
                # 研究資料検索・発見結果の処理
                logger.info(f"[ResponseFormatter] DiscoveryAgent block entered")
                logger.info(f"[ResponseFormatter] DiscoveryAgent result.get('success', True): {result.get('success', True)}")
                if result.get("success", True):  # DiscoveryAgentはデフォルトでsuccess
                    logger.info(f"[ResponseFormatter] DiscoveryAgent success condition passed")
                    response = "✅ ChromaDB資料検索タスクが完了しました！\n\n"

                    # 検索情報
                    query = result.get("query", "")
                    search_type = result.get("search_type", "semantic")
                    total_results = result.get("total_results", 0)

                    response += f"🔍 実行内容:\n"
                    response += f"- 検索クエリ: 「{query[:50]}...」\n" if len(query) > 50 else f"- 検索クエリ: 「{query}」\n"
                    response += f"- 検索方式: {search_type}\n"
                    response += f"- 発見資料数: {total_results}件\n\n"

                    # 検索結果サマリー
                    summary = result.get("summary", "")
                    if summary:
                        response += f"📊 検索結果サマリー:\n{summary}\n\n"

                    # 上位結果の表示
                    results = result.get("results", [])
                    if results:
                        response += "📚 発見した関連資料（上位3件）:\n\n"
                        for idx, item in enumerate(results[:3], 1):
                            rank = item.get("rank", idx)
                            relevance_score = item.get("relevance_score", 0)
                            content = item.get("content", "")
                            metadata = item.get("metadata", {})
                            filename = metadata.get("filename", "不明")

                            response += f"{rank}. 関連度: {relevance_score:.1%}\n"
                            response += f"   出典: {filename}\n"
                            if content:
                                content_preview = content[:150].replace('\n', ' ')
                                response += f"   内容: {content_preview}...\n"
                            response += "\n"

                        if total_results > 3:
                            response += f"（他 {total_results - 3}件の関連資料が見つかりました）"
                    else:
                        response += "💡 該当する資料が見つかりませんでした。検索条件を変更してお試しください。"

                    logger.info(f"[ResponseFormatter] DiscoveryAgent response length: {len(response)}")
                    final_message_parts.append(response)
                    logger.info(f"[ResponseFormatter] DiscoveryAgent message appended. Current parts count: {len(final_message_parts)}")
                    task_summaries["discovery"] = "完了"

            elif agent_name == "StrategyAgent":
                # 研究戦略立案結果の処理
                if result.get("success", False):
                    response = "✅ 研究戦略立案タスクが完了しました！\n\n"

                    task_type = result.get("task_type", "strategy")
                    strategy_result = result.get("strategy_result", {})

                    # 戦略プラン
                    strategy_plan = strategy_result.get("strategy_plan", result.get("strategy_plan", ""))
                    if strategy_plan:
                        response += "📋 戦略プラン:\n"
                        if len(strategy_plan) > 300:
                            response += f"{strategy_plan[:300]}...\n\n"
                        else:
                            response += f"{strategy_plan}\n\n"

                    # 戦略的推奨事項
                    recommendations = strategy_result.get("strategic_recommendations", result.get("strategic_recommendations", []))
                    if recommendations:
                        response += "💡 戦略的推奨事項:\n"
                        for i, rec in enumerate(recommendations[:5], 1):
                            response += f"{i}. {rec}\n"
                        response += "\n"

                    # リスク評価
                    risk_assessment = strategy_result.get("risk_assessment", result.get("risk_assessment", {}))
                    if risk_assessment:
                        risk_level = risk_assessment.get("risk_level", "中")
                        response += f"⚠️ リスクレベル: {risk_level}\n"

                        mitigations = risk_assessment.get("mitigation_strategies", [])
                        if mitigations:
                            response += "\n軽減戦略:\n"
                            for i, mitigation in enumerate(mitigations[:3], 1):
                                response += f"{i}. {mitigation}\n"

                    final_message_parts.append(response)
                    task_summaries["strategy"] = "完了"

            elif agent_name == "OptimizationAgent":
                # 研究最適化結果の処理
                if result.get("success", False):
                    response = "✅ 研究最適化タスクが完了しました！\n\n"

                    task_type = result.get("task_type", "optimization")
                    optimization_result = result.get("optimization_result", {})

                    # 最適化提案
                    proposals = optimization_result.get("optimization_proposals", result.get("optimization_proposals", []))
                    if proposals:
                        response += "🎯 最適化提案:\n"
                        for i, proposal in enumerate(proposals[:5], 1):
                            response += f"{i}. {proposal}\n"
                        response += "\n"

                    # 効率化指標
                    metrics = optimization_result.get("efficiency_metrics", result.get("efficiency_metrics", {}))
                    if metrics:
                        response += "📊 効率化指標:\n"
                        if "time_savings" in metrics:
                            response += f"- 時間短縮: {metrics['time_savings']}\n"
                        if "cost_reduction" in metrics:
                            response += f"- コスト削減: {metrics['cost_reduction']}\n"
                        if "quality_improvement" in metrics:
                            response += f"- 品質向上: {metrics['quality_improvement']}\n"
                        response += "\n"

                    # 実装優先度
                    priority_list = optimization_result.get("implementation_priority", result.get("implementation_priority", []))
                    if priority_list:
                        response += "📌 実装優先度:\n"
                        for i, item in enumerate(priority_list[:5], 1):
                            response += f"{i}. {item}\n"

                    final_message_parts.append(response)
                    task_summaries["optimization"] = "完了"

        # 最終メッセージの組み立て
        logger.info(f"[ResponseFormatter] Final message_parts count: {len(final_message_parts)}")
        for idx, part in enumerate(final_message_parts):
            logger.info(f"[ResponseFormatter] Part {idx} length: {len(part)}, preview: {part[:100] if len(part) > 100 else part}")

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