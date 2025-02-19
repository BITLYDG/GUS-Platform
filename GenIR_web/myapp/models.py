from django.db import models
from django.contrib.auth import get_user_model  # 添加用户模型引用

User = get_user_model()  # 获取当前用户模型

class DialogueAnnotation(models.Model):
    QUALITY_CHOICES = [
        (1, '1分 - 质量差'),
        (2, '2分 - 质量一般'),
        (3, '3分 - 质量良好'),
        (4, '4分 - 质量优秀'),
        (5, '5分 - 质量完美'),
    ]

    task = models.ForeignKey(
        'TaskData',
        on_delete=models.CASCADE,
        related_name='annotations',
        verbose_name="关联任务"
    )
    dialogue_id = models.CharField(max_length=50, verbose_name="对话ID")
    response_id = models.CharField(max_length=50, verbose_name="回复ID")
    quality_score = models.IntegerField(
        choices=QUALITY_CHOICES,
        verbose_name="质量评分"
    )
    annotation_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="标注备注"
    )
    annotator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="标注人员"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'dialogue_id', 'response_id', 'annotator')
        verbose_name = '对话标注'
        verbose_name_plural = '对话标注'

    def __str__(self):
        return f"{self.task} - {self.dialogue_id}.{self.response_id}"

# models.py
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
    created_at = models.DateTimeField(auto_now_add=True)
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
        返回与当前任务关联的第一条 DialogueAnnotation 数据，
        便于在列表页中显示标注人。
        """
        return self.annotations.first()

    class Meta:
        ordering = ['-created_at']
        verbose_name = '任务数据'
        verbose_name_plural = '任务数据'

class LinkScore(models.Model):
    task = models.ForeignKey(
        'TaskData',
        on_delete=models.CASCADE,
        related_name='link_scores',
        verbose_name="关联任务"
    )
    link_index = models.IntegerField(verbose_name="链接索引")
    score = models.IntegerField(verbose_name="评分")
    annotator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="评分人员"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'link_index', 'annotator')
        verbose_name = '链接评分'
        verbose_name_plural = '链接评分'

    def __str__(self):
        return f"{self.task} - Link {self.link_index}: Score {self.score}"