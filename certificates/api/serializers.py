from rest_framework import serializers
from ..models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['id', 'user', 'amount', 'code', 'is_used', 'purchase_date', 'used_date']
        read_only_fields = ['code', 'purchase_date', 'used_date']

    def create(self, validated_data):
        # Generate unique code for the certificate
        import uuid
        validated_data['code'] = str(uuid.uuid4())[:8].upper()
        return super().create(validated_data) 