from pydantic import BaseModel, Field


class ListForTransferRequest(BaseModel):
    asking_price: int = Field(gt=0)


class SetLineupRequest(BaseModel):
    """Any field left null gets auto-filled server-side with the best
    available player at that position -- a slot doesn't need an explicit
    pick to be saved."""

    qb_id: int | None = None
    rb_ids: list[int | None] = [None, None]
    wr_ids: list[int | None] = [None, None]
    te_id: int | None = None
    def_id: int | None = None
    k_id: int | None = None
