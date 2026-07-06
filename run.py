import bypass
import asyncio

if __name__ == "__main__":
    try:
        asyncio.run(bypass.main())
    except KeyboardInterrupt:
        import sys
        sys.exit(0)
