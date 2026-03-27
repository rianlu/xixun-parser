import sys
import os
import json
import readline # For better input handling

# Ensure we can import backend modules (Add root dir to sys.path)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

try:
    from backend.parser import WeChatArticleParser
    from backend.sync_to_feishu import FeishuSync
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def print_colored(text, color_code):
    """Print text with ANSI color codes"""
    print(f"\033[{color_code}m{text}\033[0m")

def main():
    print_colored("\n=== 🎭 戏讯一键解析同步工具 ===", "1;36") # Cyan
    
    # 1. Input URL
    args = sys.argv[1:]
    auto_confirm = False
    if "-y" in args:
        auto_confirm = True
        args.remove("-y")
    if "--yes" in args:
        auto_confirm = True
        args.remove("--yes")

    if args:
        url = args[0]
    else:
        try:
            url = input("\n请输入微信公众号文章链接: ").strip()
        except KeyboardInterrupt:
            print("\n已退出")
            return 1
    
    if not url:
        print_colored("❌ 未输入链接，退出。", "31")
        return 1

    # 2. Parse
    print_colored(f"\n🚀 正在解析: {url} ...", "33") # Yellow
    
    try:
        # Use headless=True for CLI (no browser window needed usually, unless debugging)
        # But if WeChat blocks headless, we might need False. 
        # The parser script defaults to headless=True.
        # Note: The parser initializes webdriver.
        with WeChatArticleParser(headless=True) as parser:
             result = parser.parse_article(url)
    except Exception as e:
        print_colored(f"❌ 解析过程出错: {e}", "31")
        return 1

    if not result.get('success'):
        print_colored(f"❌ 解析失败: {result.get('error')}", "31")
        return 1

    performances = result['data']['performances']
    print_colored(f"✅ 解析成功! 共提取到 {len(performances)} 条数据。", "32")

    # Filter by Default Regions (replicating web UI defaults)
    DEFAULT_REGIONS = ['龙港', '平阳', '苍南']
    print_colored(f"\n🔍 正在根据默认地区筛选: {', '.join(DEFAULT_REGIONS)}", "36")
    
    filtered_performances = []
    for p in performances:
        venue = p.get('venue', '')
        # Check if venue contains any of the target regions
        if any(region in venue for region in DEFAULT_REGIONS):
            filtered_performances.append(p)
            
    print_colored(f"✅ 筛选包含 {len(filtered_performances)} 条有效数据 (过滤掉了 {len(performances) - len(filtered_performances)} 条)", "32")
    
    if not filtered_performances:
        print_colored("⚠️  筛选后没有剩余数据，退出。", "31")
        return 0

    # 3. Calculate Sync Plan
    print_colored("\n☁️  正在比对云端数据...", "33")
    syncer = FeishuSync()
    
    try:
        plan = syncer.calculate_sync_plan(filtered_performances)
    except Exception as e:
        print_colored(f"❌ 比对失败: {e}", "31")
        return 1

    actions = plan['actions']
    
    to_create = [a for a in actions if a['type'] == 'CREATE']
    to_update = [a for a in actions if a['type'] == 'UPDATE']
    to_delete = [a for a in actions if a['type'] == 'DELETE']
    to_skip = [a for a in actions if a['type'] == 'SKIP']
    
    # 4. Display Preview
    print_colored("\n📊 同步预览", "1;34")
    print(f"云端现有: {plan['remote_count']} 条")
    print(f"本次新增: \033[32m{len(to_create)}\033[0m 条")
    print(f"本次更新: \033[33m{len(to_update)}\033[0m 条")
    print(f"保留数据: {len(to_skip)} 条 (无变动或受保护)")
    if to_delete:
         print(f"将被清理: \033[31m{len(to_delete)}\033[0m 条 (旧System数据)")

    if not to_create and not to_update and not to_delete:
        print_colored("\n✨ 数据已是最新，无需同步。", "32")
        return 0

    # Show details for Create and Update
    if to_create:
        print_colored("\n[➕ 新增列表]", "32")
        for a in to_create:
             print(f"  + {a['troupe']} @ {a['venue']} ({a['date']})")

    if to_update:
        print_colored("\n[🔄 更新列表]", "33")
        for a in to_update:
            print(f"  * {a['troupe']} ({a['date']})")
            if a.get('old_venue') != a.get('venue'):
                print(f"    📍 地址: \033[9m{a.get('old_venue') or '空'}\033[0m -> {a['venue']}")
            if a.get('old_end_date') != a.get('end_date'):
                 print(f"    📅 结束: \033[9m{a.get('old_end_date') or '空'}\033[0m -> {a.get('end_date')}")
            if a.get('old_content') != a.get('content'):
                 print(f"    📝 内容: (已变更)")

    if to_delete:
        # Show delete summary but maybe not all if there are many?
        # User previously wanted to hide delete details in UI, but CLI might differ.
        # Let's show first 5 and summary if more.
        print_colored(f"\n[🗑️  移除列表] ({len(to_delete)}条)", "31")
        for i, a in enumerate(to_delete):
            if i < 5:
                print(f"  - {a['troupe']} @ {a['venue']} ({a['date']})")
            else:
                print(f"  ... 以及其他 {len(to_delete)-5} 条")
                break

    # 5. Confirm
    print("\n")
    if auto_confirm:
        print_colored("🤖 已启用自动确认 (--yes)，跳过手动确认步骤。", "36")
        confirm = 'y'
    else:
        try:
            confirm = input("❓ 是否确认执行同步? (y/N): ").strip().lower()
        except KeyboardInterrupt:
            print("\n已取消")
            return 1

    if confirm == 'y':
        print_colored("\n🔄 正在执行同步...", "33")
        try:
            stats = syncer.execute_sync_plan(actions)
            print_colored(f"\n✅ 同步完成!", "1;32")
            print(f"新增: {stats['create']}")
            print(f"更新: {stats['update']}")
            print(f"删除: {stats['delete']}")
            return 0
        except Exception as e:
            print_colored(f"❌ 同步执行失败: {e}", "31")
            return 1
    else:
        print_colored("🚫 已取消操作。", "37")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
