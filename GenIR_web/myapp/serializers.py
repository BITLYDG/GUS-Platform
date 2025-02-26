from rest_framework import serializers
from .models import TaskData


class TaskDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskData
        fields = ['id', 'user', 'dialogue', 'behavior', 'metadata', 'created_at', 'annotated']
        read_only_fields = ['created_at', 'annotated', 'user']  # 将 user 添加到只读字段

    def validate_dialogue(self, value):
        """验证对话数据的格式"""
        if not isinstance(value, list):
            raise serializers.ValidationError("对话数据必须是数组格式")

        # 验证每个对话记录的结构
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("每个对话记录必须是字典格式")

            required_fields = ['queryId', 'queryText', 'responses', 'timestamp']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"对话记录缺少必要字段: {field}")

        return value

    def validate_behavior(self, value):
        """验证行为数据的格式"""
        required_fields = ['startTime', 'endTime', 'dwellTime', 'pageViews', 'clicks']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"行为数据缺少必要字段: {field}")
        return value

    def validate_metadata(self, value):
        """验证元数据的格式"""
        required_fields = ['timestamp', 'userAgent']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"元数据缺少必要字段: {field}")
        return value

    def create(self, validated_data):
        # 添加详细的用户检测调试信息
        # print("\n=== 用户检测调试信息 ===")

        # 获取请求上下文
        request = self.context.get('request')
        # print(f"请求上下文是否存在: {request is not None}")

        # 检查用户属性
        if request:
            # print(f"请求对象是否有 'user' 属性: {hasattr(request, 'user')}")

            if hasattr(request, 'user'):
                user = request.user
                # print(f"用户是否已认证: {user.is_authenticated}")
                # print(f"用户ID: {user.id if user.is_authenticated else '未认证'}")

                # 仅在用户已认证时添加用户ID
                if user.is_authenticated:
                    validated_data['user'] = user
                    # print(f"已添加用户ID: {user.id}")

        # print("=== 用户检测结束 ===\n")

        return super().create(validated_data)