import requests
import json
import os
import time
from datetime import datetime

# 配置请求头（模拟浏览器）
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://pvp.qq.com/web201605/herodetail.shtml'  # 英雄详情页面的来源
}

# 创建知识库文件夹
os.makedirs("", exist_ok=True)

print("=" * 50)
print("开始获取王者荣耀数据")
print("=" * 50)

# 1. 获取装备数据
print("\n[1/3] 正在获取装备数据...")
item_url = "https://pvp.qq.com/web201605/js/item.json"
try:
    response = requests.get(item_url, headers=headers)
    items = response.json()
    print(f"   成功获取 {len(items)} 件装备数据")

    # 装备类型映射
    item_type_dict = {1: '攻击', 2: '法术', 3: '防御', 4: '移动', 5: '打野', 7: '游走'}

    # 按类型保存装备信息
    for item in items:
        item_id = item.get('item_id')
        item_name = item.get('item_name')
        item_type = item_type_dict.get(item.get('item_type'), '其他')
        price = item.get('price')
        total_price = item.get('total_price')
        des1 = item.get('des1', '').replace('<p>', '').replace('</p>', '')
        des2 = item.get('des2', '').replace('<p>', '').replace('</p>', '')

        content = f"""【装备名称】{item_name}
【装备类型】{item_type}
【售价】{price}
【总价】{total_price}
【基础属性】{des1}
【装备效果】{des2}
"""
        filename = f"./王者知识库/{item_type}装备.txt"
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(content)
            f.write("\n" + "-" * 50 + "\n\n")

    print("   装备数据已保存到 ./王者知识库/")
except Exception as e:
    print(f"   装备数据获取失败：{e}")

# 2. 获取英雄列表
print("\n[2/3] 正在获取英雄列表...")
herolist_url = "https://pvp.qq.com/web201605/js/herolist.json"
try:
    response = requests.get(herolist_url, headers=headers)
    hero_list = response.json()
    print(f"   成功获取 {len(hero_list)} 个英雄信息")

    # 提取英雄ID和名称
    heroes = [{'ename': h['ename'], 'cname': h['cname']} for h in hero_list]
    print(f"   英雄ID范围：{heroes[0]['ename']} ~ {heroes[-1]['ename']}")
except Exception as e:
    print(f"   英雄列表获取失败：{e}")
    heroes = []
    # 如果列表获取失败，使用之前的手动ID作为后备
    fallback_ids = [154, 191, 105, 508, 123, 190, 501, 515, 518, 529]
    heroes = [{'ename': hid, 'cname': f'英雄{hid}'} for hid in fallback_ids]
    print(f"   使用后备英雄ID列表：{fallback_ids}")

# 3. 获取每个英雄的详细信息
print("\n[3/3] 正在获取英雄详细信息...")
success_count = 0
hero_details = []

for hero in heroes:
    hero_id = hero['ename']
    hero_name = hero['cname']
    detail_url = f"https://pvp.qq.com/web201605/js/hero/{hero_id}.json"

    try:
        # 添加延时避免请求过快
        time.sleep(0.2)

        resp = requests.get(detail_url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()

            # 提取英雄故事
            info = data.get('info', {})
            story = info.get('story', {})
            # 故事可能有两种结构：'故事' 或 'shortStory'
            story_text = story.get('故事', story.get('shortStory', '暂无故事'))

            # 提取推荐出装
            rec_item = info.get('rec_item', [])
            rec_item_str = '、'.join(rec_item) if rec_item else '暂无推荐出装'

            # 提取英雄定位（可能有多个）
            hero_type = info.get('hero_type', [])
            hero_type_str = '、'.join([str(t) for t in hero_type]) if hero_type else '未知'

            # 组装内容
            content = f"""【英雄名称】{hero_name}
【英雄ID】{hero_id}
【英雄定位】{hero_type_str}
【英雄故事】{story_text}
【推荐出装】{rec_item_str}
"""
            # 保存到英雄攻略文件
            with open("./王者知识库/英雄攻略.txt", 'a', encoding='utf-8') as f:
                f.write(content)
                f.write("\n" + "-" * 50 + "\n\n")

            success_count += 1
            hero_details.append(hero_name)
            print(f"   ✓ {hero_name} (ID:{hero_id}) 获取成功")
        else:
            print(f"   ✗ {hero_name} (ID:{hero_id}) 返回状态码 {resp.status_code}")
    except Exception as e:
        print(f"   ✗ {hero_name} (ID:{hero_id}) 获取失败：{type(e).__name__}")

print(f"\n英雄详细信息获取完成：成功 {success_count} 个，失败 {len(heroes) - success_count} 个")
if success_count > 0:
    print(f"已保存英雄：{', '.join(hero_details[:5])}{'...' if len(hero_details) > 5 else ''}")

# 4. 生成知识库总览
print("\n正在生成知识库总览...")
with open("README.txt", 'w', encoding='utf-8') as f:
    f.write(f"""王者荣耀玩法知识库
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

数据来源：王者荣耀官网
包含内容：
- 攻击装备 {len([i for i in items if item_type_dict.get(i.get('item_type')) == '攻击'])}件
- 法术装备 {len([i for i in items if item_type_dict.get(i.get('item_type')) == '法术'])}件
- 防御装备 {len([i for i in items if item_type_dict.get(i.get('item_type')) == '防御'])}件
- 移动装备 {len([i for i in items if item_type_dict.get(i.get('item_type')) == '移动'])}件
- 打野装备 {len([i for i in items if item_type_dict.get(i.get('item_type')) == '打野'])}件
- 游走装备 {len([i for i in items if item_type_dict.get(i.get('item_type')) == '游走'])}件
- 英雄攻略 {success_count}篇（成功获取的）

可用问题示例：
- "攻击装备有哪些？"
- "破军的属性是什么？"
- "法师应该出什么装备？"
- "澜的推荐出装是什么？"
- "赵云的故事是什么？"
""")

print("\n✅ 知识库构建完成！")
print("请查看 ./王者知识库/ 文件夹")