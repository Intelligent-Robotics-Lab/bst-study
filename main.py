import asyncio
import logic.bst as bst

async def main():
    await bst.BST()

if __name__ == "__main__":
    asyncio.run(main())