"""B站登录凭证配置助手"""
import json
from pathlib import Path


def main():
    """交互式配置凭证"""
    print("\n" + "=" * 60)
    print("  B站登录凭证配置助手")
    print("=" * 60)
    print("\n⚠️  凭证获取方法：")
    print("  1. 浏览器访问 https://www.bilibili.com 并登录")
    print("  2. 按F12打开开发者工具")
    print("  3. Application → Cookies → https://www.bilibili.com")
    print("  4. 找到并复制以下字段的值")
    print("\n详细图文教程请查看: HOW_TO_GET_CREDENTIALS.md\n")

    # 获取用户输入
    print("=" * 60)
    print("请输入凭证信息：")
    print("=" * 60)

    sessdata = input("\n1. SESSDATA (必需): ").strip()

    if not sessdata or sessdata == "":
        print("\n❌ 错误：SESSDATA是必需的！")
        print("   请重新运行脚本并提供有效的SESSDATA")
        return

    print("\n2. bili_jct (可选，直接回车跳过): ", end="")
    bili_jct = input().strip()

    print("3. buvid3 (可选，直接回车跳过): ", end="")
    buvid3 = input().strip()

    # 构造配置
    config = {
        "comment": "B站登录凭证配置 - 由setup_credentials.py自动生成",
        "sessdata": sessdata,
        "bili_jct": bili_jct if bili_jct else "",
        "buvid3": buvid3 if buvid3 else "",
        "note": "获取方法：浏览器登录bilibili.com，F12开发者工具 → Application → Cookies"
    }

    # 保存到文件
    config_file = Path(__file__).parent / "credentials.json"

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print("✅ 凭证配置成功！")
        print("=" * 60)
        print(f"\n配置已保存到: {config_file}")
        print("\n提供的凭证：")
        print(f"  ✓ SESSDATA: {sessdata[:20]}... (已截断)")
        if bili_jct:
            print(f"  ✓ bili_jct: {bili_jct[:20]}...")
        else:
            print("  ⚠ bili_jct: 未提供")
        if buvid3:
            print(f"  ✓ buvid3: {buvid3[:20]}...")
        else:
            print("  ⚠ buvid3: 未提供")

        print("\n下一步：")
        print("  1. 运行测试验证凭证:")
        print("     python test_refactored_service.py")
        print("\n  2. 启动服务:")
        print("     uvicorn app.main:app --reload")

    except Exception as e:
        print(f"\n❌ 保存配置失败: {e}")
        print("请检查文件权限并重试")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  配置已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
