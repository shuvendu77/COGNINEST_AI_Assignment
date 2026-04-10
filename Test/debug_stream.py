import asyncio
from vanna_setup import setup_vanna
from vanna.core.user import RequestContext

async def test():
    agent, memory = setup_vanna()
    context = RequestContext()
    print("--- Components yielded ---")
    async for comp in agent.send_message(context, "How many patients do we have?"):
        rc = comp.rich_component
        sc = comp.simple_component
        rc_content = getattr(rc, "content", None)
        rc_metadata = getattr(rc, "metadata", None)
        print(f"  RC type={rc.type} class={type(rc).__name__}", end="")
        if rc_content:
            print(f" content={repr(rc_content[:80])}", end="")
        if rc_metadata:
            print(f" metadata_keys={list(rc_metadata.keys())}", end="")
        print()
        if sc:
            sc_text = getattr(sc, "text", None)
            print(f"  SC class={type(sc).__name__} text={repr(sc_text[:80]) if sc_text else None}")

asyncio.run(test())
