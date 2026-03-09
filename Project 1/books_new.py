from typing import List, Optional
from fastapi import FastAPI, Path, Query, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Library Management System", version="1.0.0")

# --- 定義資料模型 (Data Models) ---
class Book(BaseModel):
    title: str = Field(..., min_length=1, example="Python Tutorial")
    author: str = Field(..., min_length=1, example="John Doe")
    category: str = Field(..., min_length=1, example="technology")

class BookUpdate(BaseModel):
    author: Optional[str] = None
    category: Optional[str] = None

# --- 模擬資料庫 ---
BOOKS = [
    {'title': 'Title One', 'author': 'Author One', 'category': 'science'},
    {'title': 'Title Two', 'author': 'Author Two', 'category': 'science'},
    {'title': 'Title Three', 'author': 'Author Three', 'category': 'history'},
]

# --- API Endpoints ---

@app.get("/books", response_model=List[dict], tags=["Books"])
async def get_all_books():
    """取得庫存中所有的書籍清單"""
    return BOOKS

@app.get("/books/{book_title}", tags=["Books"])
async def get_book_by_title(book_title: str = Path(..., description="要搜尋的書名")):
    """根據書名查詢書籍 (忽略大小寫)"""
    for book in BOOKS:
        if book['title'].casefold() == book_title.casefold():
            return book
    raise HTTPException(status_code=404, detail="Book not found")

@app.get("/books/", tags=["Books"])
async def filter_books(
    category: Optional[str] = Query(None, description="按分類篩選"),
    author: Optional[str] = Query(None, description="按作者篩選")
):
    """靈活篩選：可根據分類、作者或兩者同時篩選"""
    results = BOOKS
    if category:
        results = [b for b in results if b['category'].casefold() == category.casefold()]
    if author:
        results = [b for b in results if b['author'].casefold() == author.casefold()]

    return results

@app.post("/books", status_code=status.HTTP_201_CREATED, tags=["Books"])
async def create_book(book: Book):
    """新增一本書籍，會自動驗證輸入欄位"""
    new_book = book.dict()
    BOOKS.append(new_book)
    return {"message": "Book created successfully", "data": new_book}

@app.put("/books/{book_title}", tags=["Books"])
async def update_book(book_title: str, updated_data: Book):
    """根據書名更新書籍資訊"""
    for i, book in enumerate(BOOKS):
        if book['title'].casefold() == book_title.casefold():
            BOOKS[i] = updated_data.dict()
            return {"message": "Book updated", "data": BOOKS[i]}
    raise HTTPException(status_code=404, detail="Book not found to update")

@app.delete("/books/{book_title}", tags=["Books"])
async def delete_book(book_title: str):
    """從清單中刪除特定書籍"""
    for i, book in enumerate(BOOKS):
        if book['title'].casefold() == book_title.casefold():
            deleted_book = BOOKS.pop(i)
            return {"message": f"Book '{book_title}' deleted successfully"}
    raise HTTPException(status_code=404, detail="Book not found to delete")