from typing import List, Optional
from fastapi import FastAPI, Path, Query, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Pro Library API", description="進階圖書管理系統")


'''統一模型：不再分 Book 類別和 BookRequest，全部使用 Pydantic，這能更完美的處理 JSON 序列化。
邏輯解耦：將搜尋邏輯改為更 Pythonic 的方式（使用 next 或列表推導）。
更嚴謹的 ID 處理：解決手動更新 ID 的潛在問題。
清晰的標籤與文件：加入 tags 與 API 說明。'''

# --- 1. 精裝版資料模型 (Schema) ---
class Book(BaseModel):
    id: Optional[int] = Field(None, description="ID 自動生成，新增時可不填")
    title: str = Field(..., min_length=3, example="Mastering FastAPI")
    author: str = Field(..., min_length=1, example="John Doe")
    description: str = Field(..., min_length=1, max_length=100)
    rating: int = Field(..., ge=1, le=5, description="評分 1 到 5 分")
    published_date: int = Field(..., ge=2000, le=2030)

    class Config:
        # Pydantic V2 的寫法 (取代舊版 json_schema_extra)
        json_schema_extra = {
            "example": {
                "title": "Python Pro Guide",
                "author": "Expert Coder",
                "description": "Learn advanced Python in 24 hours.",
                "rating": 5,
                "published_date": 2024
            }
        }

# --- 2. 模擬資料庫 (直接存儲 Pydantic 物件) ---
BOOKS: List[Book] = [
    Book(id=1, title='Computer Science Pro', author='codingwithroby', description='A nice book!', rating=5, published_date=2030),
    Book(id=2, title='Be Fast with FastAPI', author='codingwithroby', description='A great book!', rating=5, published_date=2030),
]

# --- 3. 內部輔助函式 ---
def _get_book_index(book_id: int) -> int:
    """根據 ID 尋找書籍索引，找不到則噴 404"""
    for index, book in enumerate(BOOKS):
        if book.id == book_id:
            return index
    raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

# --- 4. API 路由控制 ---

@app.get("/books", response_model=List[Book], status_code=status.HTTP_200_OK, tags=["Query"])
async def get_all_books():
    """獲取庫存中所有書籍清單"""
    return BOOKS

@app.get("/books/{book_id}", response_model=Book, tags=["Query"])
async def get_book_by_id(book_id: int = Path(..., gt=0)):
    """透過 ID 獲取特定書籍"""
    idx = _get_book_index(book_id)
    return BOOKS[idx]

@app.get("/books/filter/", response_model=List[Book], tags=["Query"])
async def filter_books(
    rating: Optional[int] = Query(None, ge=1, le=5),
    year: Optional[int] = Query(None, ge=2000, le=2030)
):
    """根據評分或年份篩選書籍"""
    results = BOOKS
    if rating:
        results = [b for b in results if b.rating == rating]
    if year:
        results = [b for b in results if b.published_date == year]
    return results

@app.post("/books", status_code=status.HTTP_201_CREATED, tags=["Action"])
async def create_new_book(book_in: Book):
    """新增書籍 (ID 將自動計算)"""
    new_id = 1 if not BOOKS else BOOKS[-1].id + 1
    book_in.id = new_id
    BOOKS.append(book_in)
    return book_in

@app.put("/books/{book_id}", status_code=status.HTTP_200_OK, tags=["Action"])
async def update_book(book_id: int, updated_book: Book):
    """更新現有書籍資訊"""
    idx = _get_book_index(book_id)
    updated_book.id = book_id  # 強制保持 ID 一致
    BOOKS[idx] = updated_book
    return {"message": "Update successful", "data": BOOKS[idx]}

@app.delete("/books/{book_id}", status_code=status.HTTP_200_OK, tags=["Action"])
async def delete_book(book_id: int = Path(..., gt=0)):
    """從系統中永久移除書籍"""
    idx = _get_book_index(book_id)
    deleted_book = BOOKS.pop(idx)
    return {"message": f"Book '{deleted_book.title}' has been deleted"}

'''
類型安全：BOOKS 現在明確定義為 List[Book]，所有操作都在 Pydantic 模型下進行，避免了舊版「清單裡有時候是 Book 類別，有時候是 BookRequest 字典」的混亂。
邏輯封裝：建立 _get_book_index 私有函式，減少重複代碼，讓主路由邏輯清晰（例如：找書、沒找到噴 404）。
遵循 RESTful 規範：
PUT 和 DELETE 通常針對具體路徑 /books/{id}。
新增資料路徑改為 POST /books。
更好的回應：DELETE 不再只回傳 204 No Content，回傳一個包含訊息的 JSON 對前端顯示「刪除成功」的訊息會更有幫助。
Pydantic V2 相容：使用了最新的 model_dump() 思路（雖然精裝版直接存物件更方便）。'''