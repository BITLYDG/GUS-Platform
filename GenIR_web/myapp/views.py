# views.py
import requests
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from flashrag.config import Config
from flashrag.dataset import Item, Dataset
from flashrag.pipeline import SequentialPipeline
from flashrag.prompt import PromptTemplate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TaskData, QueryAnnotation, LinkScore,SessionAnnotation
from .serializers import TaskDataSerializer
from django.views.generic import ListView, DetailView
from datetime import datetime
import json
import traceback
import json
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages


perplexity_key = '' # your API key


def chat(request):
    return render(request, 'chat.html')


def signup(request):
    return render(request, 'signup.html')


def signin(request):
    return render(request, 'signin.html')


def index(request):
    return render(request, 'signin.html')


from django.contrib.auth import authenticate, login

@csrf_exempt  # 禁用 CSRF 验证
def query2flashrag(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)  # 将请求体解析为字典
            query = body.get("query", "What is the capital of China?")
            model1_path = body.get("model1", "model/e5-base-v2")
            model2_path = body.get("model2", "model/Llama-3.2-1B-Instruct")
            data = [
                {"question": query, "golden_answers": [""]},
            ]
            item_objects = [Item(item_dict) for item_dict in data]
            config_dict = {
                "data_dir": "dataset/",
                "index_path": "indexes/e5_Flat.index",
                "corpus_path": "indexes/general_knowledge.jsonl",
                "model2path": {"e5": model1_path,
                               "llama3-8B-instruct": model2_path},
                "generator_model": "llama3-8B-instruct",
                "retrieval_method": "e5",
                "metrics": ["em", "f1", "acc"],
                "retrieval_topk": 1,
                "save_intermediate_data": True,
            }

            config = Config(config_dict=config_dict)
            dataset = Dataset(config=config, data=item_objects)

            prompt_templete = PromptTemplate(
                config,
                system_prompt="Answer the question based on the given document. \
                                Only give me the answer and do not output any other words. \
                                \nThe following are given documents.\n\n{reference}",
                user_prompt="Question: {question}\nAnswer:",
            )

            pipeline = SequentialPipeline(config, prompt_template=prompt_templete)

            output_dataset = pipeline.run(dataset, do_eval=True)
            return JsonResponse({"prediction": output_dataset.pred}, status=200)
        except Exception as e:
            return JsonResponse({"error": "An error occurred", "details": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)


def loginAccount(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 尝试认证用户
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # 自动创建会话和 session cookie
            return redirect('chat')
        else:
            # 如果认证失败，判断用户名是否存在
            try:
                user_obj = User.objects.get(username=username)
                # 如果用户存在，则错误可能是密码错误
                error_id = '101'
                error_msg = '密码错误，请重新输入。'
            except User.DoesNotExist:
                # 如果用户名不存在，则返回相应错误
                error_id = '102'
                error_msg = '用户名不存在。'

            context = {
                'error': error_msg,
                'error_id': error_id,
            }
            return render(request, 'signin.html', context)
    else:
        return render(request, 'signin.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 检查用户名或密码是否为空
        if not username or not password:
            # error_id '201' 表示“用户名或密码为空”
            messages.error(request, "用户名和密码不能为空！")
            return render(request, 'signup.html', {'error_id': '201'})

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            # error_id '202' 表示“用户名已存在”
            messages.error(request, "用户名已存在，请选择其他用户名。")
            return render(request, 'signup.html', {'error_id': '202'})

        # 创建新用户（create_user 会自动加密密码）
        user = User.objects.create_user(username=username, password=password)
        user.save()

        messages.success(request, "注册成功！请登录。")
        return redirect('signin')  # 假设 'signin' 是登录页面的 URL 名称
    else:
        return render(request, 'signup.html')


@csrf_exempt  # 暂时禁用 CSRF，仅用于开发测试
def perplexity_api(request):
    if request.method == "POST":
        try:
            # 从请求体中获取用户消息
            body = json.loads(request.body)
            message = body.get("conversationHistory")
            model = body.get("model", "llama-3.1-sonar-small-128k-online")
            max_tokens = body.get("max_tokens", 4096)
            return_images = body.get("return_images", False)
            return_related_questions = body.get("return_related_questions", False)
            stream = body.get("stream", False)
            temperature = body.get("temperature", 0.2)
            presence_penalty = body.get("presence_penalty", 0)
            top_k = body.get("top_k", 0)
            top_p = body.get("top_p", 0.0)

            # 定义 Perplexity API 的 URL 和请求参数
            url = "https://api.perplexity.ai/chat/completions"
            payload = {
                "messages": message,
                "model": model,
                "max_tokens": max_tokens,
                "return_images": return_images,
                "return_related_questions": return_related_questions,
                "stream": True,
                "temperature": temperature,
                "presence_penalty": presence_penalty,
                "top_k": top_k,
                "top_p": top_p,
            }
            headers = {
                "Authorization": perplexity_key, 
                "Content-Type": "application/json"
            }

            # 定义流式响应生成器
            def stream_response():
                with requests.post(url, json=payload, headers=headers, stream=True) as response:
                    if response.status_code == 200:
                        # 逐块读取流式响应
                        for chunk in response.iter_content(chunk_size=512):
                            if chunk:
                                yield chunk
                    else:
                        # 如果请求失败，返回错误信息
                        yield f"Error: {response.status_code} - {response.text}"

            # 返回流式 HTTP 响应
            return StreamingHttpResponse(stream_response(), content_type="text/plain")

        except Exception as e:
            return JsonResponse({"error": "An error occurred", "details": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)


from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name='dispatch')
class TaskDataAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    # def print_dialogue_debug(self, dialogue_data):
    #     """打印对话历史的调试信息"""
    #     print("\n=== 对话历史调试信息 ===")
    #     if not isinstance(dialogue_data, list):
    #         print("警告: dialogue_data 不是列表格式")
    #         print(f"实际数据类型: {type(dialogue_data)}")
    #         print(f"数据内容: {dialogue_data}")
    #         return

    #     print(f"对话轮次总数: {len(dialogue_data)}")

    #     for i, dialogue in enumerate(dialogue_data, 1):
    #         print(f"\n--- 第 {i} 轮对话 ---")
    #         try:
    #             # 打印查询信息
    #             print(f"Query ID: {dialogue.get('queryId', 'N/A')}")
    #             print(f"Query Text: {dialogue.get('queryText', 'N/A')}")
    #             print(f"Query Timestamp: {dialogue.get('timestamp', 'N/A')}")

    #             # 打印响应信息
    #             responses = dialogue.get('responses', [])
    #             print(f"Response 数量: {len(responses)}")
    #             for j, response in enumerate(responses, 1):
    #                 print(f"  Response {j}:")
    #                 print(f"    ID: {response.get('responseId', 'N/A')}")
    #                 print(f"    Text: {response.get('responseHTML', 'N/A')[:100]}...")  # 只打印前100个字符
    #                 print(f"    Timestamp: {response.get('timestamp', 'N/A')}")
    #         except Exception as e:
    #             print(f"处理第 {i} 轮对话时出错: {str(e)}")
    #             print(f"原始数据: {dialogue}")

    # def print_behavior_debug(self, behavior_data):
    #     """打印行为数据的调试信息"""
    #     print("\n=== 行为数据调试信息 ===")
    #     try:
    #         print(f"开始时间: {behavior_data.get('startTime', 'N/A')}")
    #         print(f"结束时间: {behavior_data.get('endTime', 'N/A')}")
    #         print(f"停留时间: {behavior_data.get('dwellTime', 'N/A')}")
    #         print(f"页面访问次数: {len(behavior_data.get('pageViews', []))}")
    #         print(f"点击次数: {len(behavior_data.get('clicks', []))}")

    #         # 打印点击详情
    #         clicks = behavior_data.get('clicks', [])
    #         if clicks:
    #             print("\n点击详情:")
    #             for i, click in enumerate(clicks, 1):
    #                 print(f"  点击 {i}:")
    #                 print(f"    时间: {click.get('timestamp', 'N/A')}")
    #                 print(f"    类型: {click.get('elementType', 'N/A')}")
    #                 print(f"    文本: {click.get('elementText', 'N/A')}")
    #                 print(f"    链接: {click.get('href', 'N/A')}")

    #                 # 新增：显示对话和链接的具体位置
    #                 dialogue_context = click.get('dialogueContext', {})
    #                 print(f"    对话索引: {dialogue_context.get('dialogueIndex', 'N/A')}")
    #                 print(f"    链接在对话中的顺序: {dialogue_context.get('linkIndexInResponse', 'N/A')}")

    #         # 打印鼠标移动详情
    #         mouse_movements = behavior_data.get('mouseMovements', [])
    #         print(f"\n鼠标移动次数: {len(mouse_movements)}")
    #         if mouse_movements:
    #             print("最近的 5 条鼠标移动记录:")
    #             for move in mouse_movements[-5:]:  # 只打印最近 5 条，避免信息过多
    #                 print(
    #                     f"  时间: {move.get('timestamp', 'N/A')}, 坐标: ({move.get('x', 'N/A')}, {move.get('y', 'N/A')})")

    #         # 打印滚动详情
    #         scroll_events = behavior_data.get('scrollEvents', [])
    #         print(f"\n滚动事件次数: {len(scroll_events)}")
    #         if scroll_events:
    #             print("最近的 5 条滚动记录:")
    #             for scroll in scroll_events[-5:]:  # 只打印最近 5 条
    #                 print(f"  时间: {scroll.get('timestamp', 'N/A')}, 滚动位置: {scroll.get('scrollY', 'N/A')}")

    #     except Exception as e:
    #         print(f"处理行为数据时出错: {str(e)}")
    #         print(f"原始数据: {behavior_data}")

    def post(self, request):
        try:
            # print("\n====== 接收到新的数据上传请求 ======")
            # print(f"请求时间: {datetime.now().isoformat()}")

            # # 打印原始请求数据的基本信息
            # print("\n=== 请求数据概览 ===")
            # print(f"数据类型: {type(request.data)}")
            # print(f"包含的键: {request.data.keys()}")

            # 详细打印对话历史
            dialogue_data = request.data.get('dialogue')
            # self.print_dialogue_debug(dialogue_data)

            # 详细打印行为数据
            behavior_data = request.data.get('behavior')
            # self.print_behavior_debug(behavior_data)

            # 数据验证和保存
            if not isinstance(dialogue_data, list):
                return Response(
                    {"error": "dialogue 必须是数组格式"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.data['user'] = request.user.id if request.user.is_authenticated else None
            serializer = TaskDataSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                instance = serializer.save()
                # print("\n=== 数据保存成功 ===")
                # print(f"记录ID: {instance.id}")

                # 验证保存的数据
                saved_instance = TaskData.objects.get(id=instance.id)
                # print("\n=== 验证保存的数据 ===")
                # print(f"保存的对话轮次: {len(saved_instance.dialogue)}")
                # print(f"第一个查询: {saved_instance.first_query}")

                return Response({
                    "message": "数据保存成功",
                    "id": instance.id,
                    "dialogueCount": len(dialogue_data)
                }, status=status.HTTP_201_CREATED)

            # print("\n=== 验证错误 ===")
            print(json.dumps(serializer.errors, indent=2))
            return Response({
                "error": "数据验证失败",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # print("\n=== 发生错误 ===")
            # print(f"错误类型: {type(e).__name__}")
            # print(f"错误信息: {str(e)}")
            # print("错误追踪:")
            # print(traceback.format_exc())

            return Response({
                "error": "服务器处理数据时出错",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # finally:
        #     print("\n====== 请求处理结束 ======\n")

from django.views.generic import DetailView
from django.http import JsonResponse

class TaskDetailView(DetailView):
    model = TaskData
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    http_method_names = ['get', 'post']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = context['task']

        unique_clicks = set()
        filtered_clicks = []

        for click in task.behavior.get('clicks', []):
            if click.get('elementType') == 'link':
                query_id = click['dialogueContext']['dialogueIndex']
                link_href = click['href']
                link_key = (query_id, link_href)

                if link_key not in unique_clicks:
                    unique_clicks.add(link_key)
                    filtered_clicks.append(click)

        context['filtered_clicks'] = filtered_clicks
        return context

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        try:
            # 处理每个对话的标注
            for dialogue in task.dialogue:
                query_id = dialogue['queryId']
                for response in dialogue['responses']:
                    response_id = response['responseId']
                    prefix = f"q_{query_id}_r_{response_id}"

                    # 收集标注数据并组织成字典
                    annotation_data = {
                        'quality_score': request.POST.get(f'quality_score_{prefix}'),
                        'relevance_score': request.POST.get(f'relevance_score_{prefix}'),
                        'completeness': request.POST.get(f'completeness_{prefix}'),
                        'clarity': request.POST.get(f'clarity_{prefix}'),
                        'required_elements': request.POST.getlist(f'required_elements_{query_id}_{response_id}[]'),
                        'annotation_comment': request.POST.get(f'annotation_comment_{prefix}'),
                        'improvement_suggestions': request.POST.get(f'improvement_suggestions_{prefix}'),
                        'question_type': request.POST.get(f'question_type_q_{query_id}')
                    }

                    # 过滤掉空值，只保存有数据的字段
                    annotation_data = {k: v for k, v in annotation_data.items() if v}

                    # 保存到数据库
                    QueryAnnotation.objects.update_or_create(
                        task=task,
                        dialogue_id=query_id,
                        response_id=response_id,
                        annotator=request.user,
                        defaults={'annotation_data': annotation_data}
                    )

            # 处理会话整体评估
            evaluation_data = {
                'satisfaction': request.POST.get('session_satisfaction'),
                'ai_success_rate': request.POST.get('ai_success_rate'),
                'search_intent': request.POST.get('search_intent'),
                'dissatisfaction_reasons': request.POST.getlist('dissatisfaction_reasons'),
                'session_notes': request.POST.get('session_notes')
            }

            # 过滤掉空值
            evaluation_data = {k: v for k, v in evaluation_data.items() if v}

            # 保存到数据库
            SessionAnnotation.objects.update_or_create(
                task=task,
                annotator=request.user,
                defaults={'evaluation_data': evaluation_data}
            )

            # 处理链接评分（保持不变）
            for click in task.behavior.get('clicks', []):
                if click.get('elementType') == 'link':
                    query_id = click['dialogueContext']['dialogueIndex']
                    link_index = click['dialogueContext']['linkIndexInResponse']
                    score_key = f"link_score_{link_index}"
                    link_score = request.POST.get(score_key)
                    if link_score is not None:
                        LinkScore.objects.update_or_create(
                            task=task,
                            query_id=query_id,
                            link_index=link_index,
                            annotator=request.user,
                            defaults={
                                'score': link_score,
                                'link_url': click.get('href', '')
                            }
                        )

            # 更新任务状态
            task.annotated = True
            task.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView


class TaskDeleteView(DeleteView):
    model = TaskData
    success_url = reverse_lazy('task-list')
    template_name = 'tasks/task_confirm_delete.html'  # 可选的确认页面


class TaskListView(ListView):
    """任务列表页"""
    model = TaskData
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 7

    def get_queryset(self):
        # 只返回当前用户的任务,并按标注状态排序
        return TaskData.objects.filter(
            user=self.request.user
        ).order_by('annotated')
