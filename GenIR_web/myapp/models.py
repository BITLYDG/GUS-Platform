from django.db import models
from django.contrib.auth import get_user_model
import time

User = get_user_model()

# 定义一个函数，用于获取当前的时间戳（毫秒级）
def current_timestamp():
    current_time = time.time_ns() // 1000000
    return current_time

class QueryAnnotation(models.Model):
    task = models.ForeignKey(
        'TaskData',
        on_delete=models.CASCADE,
        related_name='annotations',
        verbose_name="关联任务"
    )
    dialogue_id = models.CharField(max_length=50, verbose_name="对话ID")
    response_id = models.CharField(max_length=50, verbose_name="回复ID")
    annotation_data = models.JSONField(
        verbose_name="标注数据",
        default=dict,
        blank=True
    )
    annotator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="标注人员"
    )
    # 使用 BigIntegerField 存储时间戳，调用 current_timestamp 获取当前时间戳
    created_at = models.BigIntegerField(default=current_timestamp, verbose_name="创建时间戳")

    class Meta:
        unique_together = ('task', 'dialogue_id', 'response_id', 'annotator')
        verbose_name = '对话标注'
        verbose_name_plural = '对话标注'

    def __str__(self):
        return f"{self.task} - {self.dialogue_id}.{self.response_id}"

class TaskData(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name="提交用户",
        null=True,  # 允许为空，以兼容现有数据
        blank=True  # 表单验证时允许为空
    )
    dialogue = models.JSONField(verbose_name="对话数据")
    behavior = models.JSONField(verbose_name="行为数据")
    metadata = models.JSONField(verbose_name="元数据")
    # 使用 BigIntegerField 存储时间戳，调用 current_timestamp 获取当前时间戳
    created_at = models.BigIntegerField(default=current_timestamp, verbose_name="创建时间戳")
    annotated = models.BooleanField(default=False, verbose_name="已标注")

    def __str__(self):
        # 更新字符串表示，包含用户信息
        user_info = f"by {self.user.username}" if self.user else "无用户"
        return f"Task {self.id} - {self.first_query} {user_info}"

    @property
    def first_query(self):
        """获取第一个查询作为标题"""
        try:
            if isinstance(self.dialogue, list) and self.dialogue:
                first_dialogue = self.dialogue[0]
                return first_dialogue.get('queryText', '无标题任务')
            return '无标题任务'
        except (AttributeError, IndexError, KeyError):
            return '无标题任务'

    @property
    def annotation_data(self):
        """
        返回与当前任务关联的第一条 QueryAnnotation 数据，
        便于在列表页中显示标注人。
        """
        return self.annotations.first()

    class Meta:
        ordering = ['-created_at']  # 时间戳仍然支持排序
        verbose_name = '任务数据'
        verbose_name_plural = '任务数据'

class SessionAnnotation(models.Model):
    task = models.ForeignKey(
        'TaskData',
        on_delete=models.CASCADE,
        related_name='session_evaluations',
        verbose_name="关联任务"
    )
    annotator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="标注人员"
    )
    evaluation_data = models.JSONField(
        verbose_name="评估数据",
        default=dict,
        blank=True
    )
    # 使用 BigIntegerField 存储时间戳，调用 current_timestamp 获取当前时间戳
    created_at = models.BigIntegerField(default=current_timestamp, verbose_name="创建时间戳")

    class Meta:
        unique_together = ('task', 'annotator')
        verbose_name = '会话评估'
        verbose_name_plural = '会话评估'

class LinkScore(models.Model):
    task = models.ForeignKey(
        'TaskData',
        on_delete=models.CASCADE,
        related_name='link_scores',
        verbose_name="关联任务"
    )
    query_id = models.IntegerField(verbose_name="对话轮数")  # 新增字段，表示对话轮次
    link_index = models.IntegerField(verbose_name="链接索引")
    link_url = models.URLField(
        max_length=500,
        verbose_name="链接地址",
        default=''
    )
    score = models.IntegerField(verbose_name="评分")
    annotator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="评分人员"
    )
    # 使用 BigIntegerField 存储时间戳，调用 current_timestamp 获取当前时间戳
    created_at = models.BigIntegerField(default=current_timestamp, verbose_name="创建时间戳")

    class Meta:
        unique_together = ('task', 'query_id', 'link_index', 'annotator')  # 确保唯一性
        verbose_name = '链接评分'
        verbose_name_plural = '链接评分'

    def __str__(self):
        return f"{self.task} - Dialogue {self.query_id} - Link {self.link_index}: {self.link_url}"