"""
修复脚本:将已存在的家庭成员同步到认证系统
"""

from family_agent.family_auth import FamilyAuthManager
from family_agent.core import FamilyAgentCore

# 初始化
auth = FamilyAuthManager()
agent = FamilyAgentCore(data_dir="data")

print(" 当前家庭列表:")
for fid, family in auth.families.items():
    print(f"  家庭号: {fid}")
    print(f"  名称: {family.family_name}")
    print(f"  认证系统成员: {family.members}")
    
    # 从角色管理系统获取成员
    agent_members = list(agent.members.keys())
    print(f"  角色系统成员: {agent_members}")
    
    # 同步:将角色系统中的成员添加到认证系统
    for member_name in agent_members:
        if member_name not in family.members:
            family.add_member(member_name)
            print(f"  ✅ 已添加成员: {member_name}")
    
    auth._save_families()
    print()

print("✅ 同步完成!")
print("\n现在所有家庭成员都可以登录了:")
for fid, family in auth.families.items():
    print(f"  家庭 {fid}: {family.members}")
