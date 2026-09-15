import asyncio

from app.queue.db_queue import DBQueue, Op, db_queue


async def test_thu_tu_fifo():
    """Event lay ra phai dung thu tu da day vao."""
    q = DBQueue()
    for i in range(5):
        await q.put(Op.INSERT_MOVE, {"move_index": i})

    thu_tu = []
    for _ in range(5):
        event = await q.get()
        thu_tu.append(event["data"]["move_index"])
        q.task_done()

    assert thu_tu == [0, 1, 2, 3, 4], f"Sai thu tu: {thu_tu}"
    print("[OK] Thu tu FIFO dung:", thu_tu)


async def test_op_khong_hop_le():
    """Op la khong duoc vao hang doi."""
    q = DBQueue()
    ket_qua = await q.put("xoa_het_database", {})
    assert ket_qua is False
    assert q.size() == 0
    print("[OK] Da chan op khong hop le")


async def test_hang_doi_day():
    """Hang doi day thi bo event, khong treo server."""
    q = DBQueue(maxsize=3)
    for i in range(3):
        await q.put(Op.INSERT_MOVE, {"move_index": i})

    print("     Hang doi da day, thu day them (cho ~2 giay)...")
    ket_qua = await q.put(Op.INSERT_MOVE, {"move_index": 99})

    assert ket_qua is False
    assert q.dropped() == 1
    print("[OK] Bo event khi day, so event da bo:", q.dropped())


async def test_nhieu_nguon_day_song_song():
    """Mo phong nhieu client cung ghi mot luc."""
    q = DBQueue()

    async def client(ten: str, so_nuoc: int):
        for i in range(so_nuoc):
            await q.put(Op.INSERT_MOVE, {"player": ten, "move_index": i})
            await asyncio.sleep(0)  # nhuong luot cho client khac

    await asyncio.gather(
        client("player_x", 10),
        client("player_o", 10),
        client("spectator_log", 5),
    )

    assert q.size() == 25, f"Thieu event, chi co {q.size()}"
    print("[OK] 3 nguon day song song, nhan du", q.size(), "event")


async def test_requeue():
    """Event ghi that bai duoc day lai voi retry_count tang."""
    q = DBQueue()
    await q.put(Op.INSERT_MATCH, {"id": "abc123"})

    event = await q.get()
    assert event["retry_count"] == 0

    await q.requeue(event)
    event_lai = await q.get()
    assert event_lai["retry_count"] == 1
    print("[OK] Requeue hoat dong, retry_count =", event_lai["retry_count"])


async def main():
    print("=" * 55)
    print(" TEST DBQueue - Module 3 Task 6, 7")
    print("=" * 55)

    await test_thu_tu_fifo()
    await test_op_khong_hop_le()
    await test_nhieu_nguon_day_song_song()
    await test_requeue()
    await test_hang_doi_day()

    print("=" * 55)
    print(" Tat ca test da qua")
    print(" Instance dung chung san sang, size =", db_queue.size())
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())