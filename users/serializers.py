from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from tenants.models import TenantMembership 
from core.thread_local import get_current_tenant


# ambil table User
User = get_user_model()

class TenantUserSerializer(serializers.ModelSerializer):
    
    # ambil data dari request user (yang masukin data role)
    role = serializers.CharField(write_only=True) # buat lolos validasi dan dimasukin ke role
    
    class Meta: # pengaturan (data dalam data)
        model = User
        fields = ['id', 'email', 'password', 'role'] # alur input & output
        extra_kwargs = {'password': {'write_only': True}} # biar gak bisa di GET di frontend
        
    @transaction.atomic
    def create(self, validated_data):
        role_from_request = validated_data.pop('role', None) # ambil 'role' terus balikin None untuk cegah KeyError
        password_from_request = validated_data.pop('password', None) 
        
        new_user = User(**validated_data) # unpacking dict dari serializer
        new_user.set_password(password_from_request)
        new_user.save() 
        
        # ambil tenant_id dari thread_local (loker)
        tenant_id = get_current_tenant()
        
        # taro di TenantMembeship (karena kita bikin user baru dan role ada disana)
        TenantMembership.objects.create(
            tenant_id = tenant_id,
            user_id = new_user, # ambil objectnya aja biar pythonic
            role = role_from_request
        )
        return new_user
    