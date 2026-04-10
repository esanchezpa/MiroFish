"""
图谱相关API路由
采用项目上下文机制，服务端持久化状态
"""

import os
import math
import time
import traceback
import threading
from datetime import datetime
from flask import request, jsonify

from . import graph_bp
from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger
from ..utils.locale import t, get_locale, set_locale
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus

# 获取日志器
logger = get_logger('mirofish.api')


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    if not filename or '.' not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in Config.ALLOWED_EXTENSIONS


# ============== 项目管理接口 ==============

@graph_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """
    获取项目详情
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    return jsonify({
        "success": True,
        "data": project.to_dict()
    })


@graph_bp.route('/project/list', methods=['GET'])
def list_projects():
    """
    列出所有项目
    """
    limit = request.args.get('limit', 50, type=int)
    projects = ProjectManager.list_projects(limit=limit)
    
    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects)
    })


@graph_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """
    删除项目
    """
    success = ProjectManager.delete_project(project_id)
    
    if not success:
        return jsonify({
            "success": False,
            "error": t('api.projectDeleteFailed', id=project_id)
        }), 404

    return jsonify({
        "success": True,
        "message": t('api.projectDeleted', id=project_id)
    })


@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
def reset_project(project_id: str):
    """
    重置项目状态（用于重新构建图谱）
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    # 重置到本体已生成状态
    if project.ontology:
        project.status = ProjectStatus.ONTOLOGY_GENERATED
    else:
        project.status = ProjectStatus.CREATED
    
    project.graph_id = None
    project.graph_build_task_id = None
    project.error = None
    ProjectManager.save_project(project)
    
    return jsonify({
        "success": True,
        "message": t('api.projectReset', id=project_id),
        "data": project.to_dict()
    })


# ============== 接口1：上传文件并生成本体 ==============

@graph_bp.route('/ontology/generate', methods=['POST'])
def generate_ontology():
    """
    接口1：上传文件，分析生成本体定义
    
    请求方式：multipart/form-data
    
    参数：
        files: 上传的文件（PDF/MD/TXT），可多个
        simulation_requirement: 模拟需求描述（必填）
        project_name: 项目名称（可选）
        additional_context: 额外说明（可选）
        
    返回：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "ontology": {
                    "entity_types": [...],
                    "edge_types": [...],
                    "analysis_summary": "..."
                },
                "files": [...],
                "total_text_length": 12345
            }
        }
    """
    try:
        logger.info("=== 开始生成本体定义 ===")
        
        # 获取参数
        simulation_requirement = request.form.get('simulation_requirement', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')
        
        logger.debug(f"项目名称: {project_name}")
        logger.debug(f"模拟需求: {simulation_requirement[:100]}...")
        
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationRequirement')
            }), 400
        
        # 获取上传的文件
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or all(not f.filename for f in uploaded_files):
            return jsonify({
                "success": False,
                "error": t('api.requireFileUpload')
            }), 400
        
        # 创建项目
        project = ProjectManager.create_project(name=project_name)
        project.simulation_requirement = simulation_requirement
        logger.info(f"创建项目: {project.project_id}")
        
        # 保存文件并提取文本
        document_texts = []
        all_text = ""
        
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                # 保存文件到项目目录
                file_info = ProjectManager.save_file_to_project(
                    project.project_id, 
                    file, 
                    file.filename
                )
                project.files.append({
                    "filename": file_info["original_filename"],
                    "size": file_info["size"]
                })
                
                # 提取文本
                text = FileParser.extract_text(file_info["path"])
                text = TextProcessor.preprocess_text(text)
                document_texts.append(text)
                all_text += f"\n\n=== {file_info['original_filename']} ===\n{text}"
        
        if not document_texts:
            ProjectManager.delete_project(project.project_id)
            return jsonify({
                "success": False,
                "error": t('api.noDocProcessed')
            }), 400
        
        # 保存提取的文本
        project.total_text_length = len(all_text)
        ProjectManager.save_extracted_text(project.project_id, all_text)
        logger.info(f"文本提取完成，共 {len(all_text)} 字符")
        
        # 生成本体
        logger.info("调用 LLM 生成本体定义...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None
        )
        
        # 保存本体到项目
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        logger.info(f"本体生成完成: {entity_count} 个实体类型, {edge_count} 个关系类型")
        
        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)
        logger.info(f"=== 本体生成完成 === 项目ID: {project.project_id}")
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "project_name": project.name,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "files": project.files,
                "total_text_length": project.total_text_length
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 接口2：构建图谱 ==============

@graph_bp.route('/build', methods=['POST'])
def build_graph():
    """
    接口2：根据project_id构建图谱
    
    请求（JSON）：
        {
            "project_id": "proj_xxxx",  // 必填，来自接口1
            "graph_name": "图谱名称",    // 可选
            "chunk_size": 500,          // 可选，默认500
            "chunk_overlap": 50         // 可选，默认50
        }
        
    返回：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "task_id": "task_xxxx",
                "message": "图谱构建任务已启动"
            }
        }
    """
    try:
        logger.info("=== 开始构建图谱 ===")
        
        # 检查配置
        errors = []
        if not Config.ZEP_API_KEY:
            errors.append(t('api.zepApiKeyMissing'))
        if errors:
            logger.error(f"配置错误: {errors}")
            return jsonify({
                "success": False,
                "error": t('api.configError', details="; ".join(errors))
            }), 500
        
        # 解析请求
        data = request.get_json() or {}
        project_id = data.get('project_id')
        logger.debug(f"请求参数: project_id={project_id}")
        
        if not project_id:
            return jsonify({
                "success": False,
                "error": t('api.requireProjectId')
            }), 400
        
        # 获取项目
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": t('api.projectNotFound', id=project_id)
            }), 404

        # 检查项目状态
        force = data.get('force', False)  # 强制重新构建
        
        if project.status == ProjectStatus.CREATED:
            return jsonify({
                "success": False,
                "error": t('api.ontologyNotGenerated')
            }), 400
        
        if project.status == ProjectStatus.GRAPH_BUILDING and not force:
            return jsonify({
                "success": False,
                "error": t('api.graphBuilding'),
                "task_id": project.graph_build_task_id
            }), 400
        
        # 如果强制重建，重置状态
        if force and project.status in [ProjectStatus.GRAPH_BUILDING, ProjectStatus.FAILED, ProjectStatus.GRAPH_COMPLETED]:
            project.status = ProjectStatus.ONTOLOGY_GENERATED
            project.graph_id = None
            project.graph_build_task_id = None
            project.error = None
        
        # Read config from request — with project and Config fallbacks
        graph_name = data.get('graph_name', project.name or 'MiroFish Graph')
        chunk_size = int(data.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE))
        chunk_overlap = int(data.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP))
        batch_size = int(data.get('batch_size', project.batch_size or Config.DEFAULT_BATCH_SIZE))
        boundary_min_fill_ratio = float(data.get('boundary_min_fill_ratio',
            project.boundary_min_fill_ratio or Config.DEFAULT_BOUNDARY_MIN_FILL_RATIO))
        min_chunk_chars = int(data.get('min_chunk_chars',
            project.min_chunk_chars or Config.DEFAULT_MIN_CHUNK_CHARS))
        episode_pack_size = int(data.get('episode_pack_size',
            project.episode_pack_size or Config.DEFAULT_EPISODE_PACK_SIZE))
        
        # Persist config snapshot to project
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap
        project.batch_size = batch_size
        project.boundary_min_fill_ratio = boundary_min_fill_ratio
        project.min_chunk_chars = min_chunk_chars
        project.episode_pack_size = episode_pack_size
        
        # Load extracted text
        text = ProjectManager.get_extracted_text(project_id)
        if not text:
            return jsonify({
                "success": False,
                "error": t('api.textNotFound')
            }), 400
        
        # --- Quota guardrail (pre-build) ---
        total_chars = len(text)
        effective_step = max(chunk_size - chunk_overlap, 1)
        estimated_episodes = math.ceil((total_chars - chunk_overlap) / effective_step)
        hard_stop = Config.DEFAULT_HARD_STOP_EPISODE_THRESHOLD
        warn_threshold = Config.DEFAULT_WARN_EPISODE_THRESHOLD
        
        if estimated_episodes > hard_stop:
            return jsonify({
                "success": False,
                "error": (
                    f"Build blocked: estimated episodes ({estimated_episodes:,}) exceed "
                    f"the hard stop threshold ({hard_stop:,}). "
                    f"Increase chunk_size or batch_size to reduce episode count."
                ),
                "quota_risk": "HIGH",
                "estimated_episodes": estimated_episodes,
                "hard_stop_threshold": hard_stop
            }), 400
        
        # 获取本体
        ontology = project.ontology
        if not ontology:
            return jsonify({
                "success": False,
                "error": t('api.ontologyNotFound')
            }), 400
        
        # 创建异步任务
        task_manager = TaskManager()
        task_id = task_manager.create_task(f"构建图谱: {graph_name}")
        logger.info(f"创建图谱构建任务: task_id={task_id}, project_id={project_id}")
        
        # 更新项目状态
        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        ProjectManager.save_project(project)
        
        # Capture locale before spawning background thread
        current_locale = get_locale()

        # 启动后台任务
        def build_task():
            set_locale(current_locale)
            build_logger = get_logger('mirofish.build')
            try:
                build_logger.info(f"[{task_id}] 开始构建图谱...")
                task_manager.update_task(
                    task_id, 
                    status=TaskStatus.PROCESSING,
                    message=t('progress.initGraphService')
                )
                
                # 创建图谱构建服务
                builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
                
                # Chunk text with full config
                task_manager.update_task(
                    task_id,
                    message=t('progress.textChunking'),
                    progress=5
                )
                chunks = TextProcessor.split_text(
                    text,
                    chunk_size=chunk_size,
                    overlap=chunk_overlap,
                    boundary_min_fill_ratio=boundary_min_fill_ratio,
                    min_chunk_chars=min_chunk_chars
                )
                total_chunks = len(chunks)
                build_start = time.time()
                
                # 创建图谱
                task_manager.update_task(
                    task_id,
                    message=t('progress.creatingZepGraph'),
                    progress=10
                )
                graph_id = builder.create_graph(name=graph_name)
                
                # 更新项目的graph_id
                project.graph_id = graph_id
                ProjectManager.save_project(project)
                
                # 设置本体
                task_manager.update_task(
                    task_id,
                    message=t('progress.settingOntology'),
                    progress=15
                )
                builder.set_ontology(graph_id, ontology)
                
                # 添加文本（progress_callback 签名是 (msg, progress_ratio)）
                def add_progress_callback(msg, progress_ratio):
                    progress = 15 + int(progress_ratio * 40)  # 15% - 55%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )
                
                task_manager.update_task(
                    task_id,
                    message=t('progress.addingChunks', count=total_chunks),
                    progress=15
                )
                
                # FIXED (v0.2): batch_size is now configurable — was hardcoded to 3
                episode_uuids = builder.add_text_batches(
                    graph_id,
                    chunks,
                    batch_size=batch_size,
                    progress_callback=add_progress_callback
                )
                
                # 等待Zep处理完成（查询每个episode的processed状态）
                task_manager.update_task(
                    task_id,
                    message=t('progress.waitingZepProcess'),
                    progress=55
                )
                
                def wait_progress_callback(msg, progress_ratio):
                    progress = 55 + int(progress_ratio * 35)  # 55% - 90%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )
                
                builder._wait_for_episodes(episode_uuids, wait_progress_callback)
                
                # 获取图谱数据
                task_manager.update_task(
                    task_id,
                    message=t('progress.fetchingGraphData'),
                    progress=95
                )
                graph_data = builder.get_graph_data(graph_id)
                
                # 更新项目状态
                project.status = ProjectStatus.GRAPH_COMPLETED
                ProjectManager.save_project(project)
                
                node_count = graph_data.get("node_count", 0)
                edge_count = graph_data.get("edge_count", 0)
                build_elapsed_ms = int((time.time() - build_start) * 1000)
                actual_batches = math.ceil(total_chunks / batch_size)
                
                build_logger.info(f"[{task_id}] Graph build complete: graph_id={graph_id}, nodes={node_count}, edges={edge_count}")
                
                # Save real build stats to project
                project.build_stats = {
                    "actual_chunks": total_chunks,
                    "actual_batches": actual_batches,
                    "actual_episodes": len(episode_uuids),
                    "node_count": node_count,
                    "edge_count": edge_count,
                    "build_elapsed_ms": build_elapsed_ms,
                    "chunk_size_used": chunk_size,
                    "chunk_overlap_used": chunk_overlap,
                    "batch_size_used": batch_size,
                    "boundary_min_fill_ratio_used": boundary_min_fill_ratio,
                    "min_chunk_chars_used": min_chunk_chars,
                    "last_run_at": datetime.now().isoformat()
                }
                
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message=t('progress.graphBuildComplete'),
                    progress=100,
                    result={
                        "project_id": project_id,
                        "graph_id": graph_id,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "chunk_count": total_chunks,
                        "batch_count": actual_batches,
                        "build_elapsed_ms": build_elapsed_ms
                    }
                )
                
                # Persist stats
                project.status = ProjectStatus.GRAPH_COMPLETED
                ProjectManager.save_project(project)
                
            except Exception as e:
                # 更新项目状态为失败
                build_logger.error(f"[{task_id}] 图谱构建失败: {str(e)}")
                build_logger.debug(traceback.format_exc())
                
                project.status = ProjectStatus.FAILED
                project.error = str(e)
                ProjectManager.save_project(project)
                
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=t('progress.buildFailed', error=str(e)),
                    error=traceback.format_exc()
                )
        
        # 启动后台线程
        thread = threading.Thread(target=build_task, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "task_id": task_id,
                "message": t('api.graphBuildStarted', taskId=task_id)
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 任务查询接口 ==============

@graph_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """
    查询任务状态
    """
    task = TaskManager().get_task(task_id)
    
    if not task:
        return jsonify({
            "success": False,
            "error": t('api.taskNotFound', id=task_id)
        }), 404
    
    return jsonify({
        "success": True,
        "data": task.to_dict()
    })


@graph_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """
    列出所有任务
    """
    tasks = TaskManager().list_tasks()
    
    return jsonify({
        "success": True,
        "data": [t.to_dict() for t in tasks],
        "count": len(tasks)
    })


# ============== 图谱数据接口 ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
def get_graph_data(graph_id: str):
    """
    获取图谱数据（节点和边）
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)
        
        return jsonify({
            "success": True,
            "data": graph_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id: str):
    """
    删除Zep图谱
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        builder.delete_graph(graph_id)
        
        return jsonify({
            "success": True,
            "message": t('api.graphDeleted', id=graph_id)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== v0.2: Estimation endpoint ==============

@graph_bp.route('/estimate', methods=['POST'])
def estimate_graph():
    """
    POST /api/graph/estimate

    Estimates chunks, episodes, batches, tokens, and time without triggering a real build.
    Does NOT require a Zep API key.

    Request (JSON):
        {
            "project_id": "proj_xxx",
            "chunk_size": 4000,      (optional, uses project/config defaults)
            "chunk_overlap": 120,
            "boundary_min_fill_ratio": 0.8,
            "min_chunk_chars": 2200,
            "batch_size": 12,
            "max_rounds_preview": 48,
            "boost_mode": "auto"
        }
    """
    try:
        data = request.get_json() or {}
        project_id = data.get('project_id')

        if not project_id:
            return jsonify({"success": False, "error": "project_id required"}), 400

        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({"success": False, "error": f"Project not found: {project_id}"}), 404

        # Config: request > project > global defaults
        chunk_size = int(data.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE))
        chunk_overlap = int(data.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP))
        batch_size = int(data.get('batch_size', project.batch_size or Config.DEFAULT_BATCH_SIZE))
        boundary_min_fill_ratio = float(data.get('boundary_min_fill_ratio',
            project.boundary_min_fill_ratio or Config.DEFAULT_BOUNDARY_MIN_FILL_RATIO))
        min_chunk_chars = int(data.get('min_chunk_chars',
            project.min_chunk_chars or Config.DEFAULT_MIN_CHUNK_CHARS))
        max_rounds_preview = int(data.get('max_rounds_preview', 48))
        boost_mode = data.get('boost_mode', 'auto')

        # Load extracted text (does NOT call Zep)
        text = ProjectManager.get_extracted_text(project_id)
        if not text:
            return jsonify({"success": False, "error": "No extracted text found. Upload files first."}), 400

        total_chars = len(text)

        # Run the REAL splitter to get exact chunk count
        chunks = TextProcessor.split_text(
            text,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
            boundary_min_fill_ratio=boundary_min_fill_ratio,
            min_chunk_chars=min_chunk_chars
        )
        exact_chunks = len(chunks)
        estimated_episodes = exact_chunks
        estimated_batches = math.ceil(exact_chunks / batch_size)

        # Quota risk assessment
        hard_stop = Config.DEFAULT_HARD_STOP_EPISODE_THRESHOLD
        warn_threshold = Config.DEFAULT_WARN_EPISODE_THRESHOLD
        if estimated_episodes >= hard_stop:
            quota_risk = "high"
        elif estimated_episodes >= warn_threshold:
            quota_risk = "medium"
        else:
            quota_risk = "low"

        # Ontology tokens (repo caps text at 50k chars for ontology LLM call)
        ontology_input_chars = min(total_chars, 50_000)
        ontology_input_tokens = math.ceil(ontology_input_chars / 3.8)
        ontology_output_tokens = max(2000, math.ceil(ontology_input_tokens * 0.18))
        ontology_total_tokens = ontology_input_tokens + ontology_output_tokens

        # Graph build time (heuristic: ~0.6-1.5s per episode including Zep processing queue)
        build_time_min = max(1, round(estimated_episodes * 0.5 / 60, 1))
        build_time_max = max(2, round(estimated_episodes * 1.5 / 60, 1))

        # Simulation tokens (heuristic: rounds × avg_agents × tokens_per_turn × platforms)
        avg_agents = 50
        avg_tokens_per_turn = 900
        platforms = 2
        sim_total_tokens = max_rounds_preview * avg_agents * avg_tokens_per_turn * platforms

        if boost_mode == 'off':
            sim_primary = sim_total_tokens
            sim_boost = 0
        else:
            sim_primary = sim_total_tokens // 2
            sim_boost = sim_total_tokens // 2

        return jsonify({
            "success": True,
            "data": {
                "total_extracted_chars": total_chars,
                "exact_chunks": exact_chunks,
                "estimated_episodes": estimated_episodes,
                "estimated_batches": estimated_batches,
                "zep_free_tier_fit": estimated_episodes < hard_stop,
                "quota_risk": quota_risk,
                "warn_threshold": warn_threshold,
                "hard_stop_threshold": hard_stop,
                "config_used": {
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "batch_size": batch_size,
                    "boundary_min_fill_ratio": boundary_min_fill_ratio,
                    "min_chunk_chars": min_chunk_chars
                },
                "ontology_tokens": {
                    "input": ontology_input_tokens,
                    "output": ontology_output_tokens,
                    "total": ontology_total_tokens,
                    "method": "heuristic",
                    "chars_sampled": ontology_input_chars
                },
                "graph_build_time_minutes": {
                    "min": build_time_min,
                    "max": build_time_max
                },
                "simulation_preview": {
                    "max_rounds": max_rounds_preview,
                    "boost_mode": boost_mode,
                    "estimated_total_tokens": sim_total_tokens,
                    "estimated_primary_tokens": sim_primary,
                    "estimated_boost_tokens": sim_boost,
                    "method": "heuristic",
                    "assumption": f"{avg_agents} agents × {avg_tokens_per_turn} tok × {platforms} platforms × {max_rounds_preview} rounds"
                },
                "last_build_stats": project.build_stats or {}
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
