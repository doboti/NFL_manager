from pydantic import BaseModel, Field


class ListForTransferRequest(BaseModel):
    asking_price: int = Field(gt=0)


class SetLineupRequest(BaseModel):
    qb_id: int
    rb_ids: list[int]
    wr_ids: list[int]
    te_id: int
    def_id: int
    k_id: int
