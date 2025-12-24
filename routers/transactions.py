from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import select
from database import SessionDep
from models import TransactionsRead, TransactionsCreate, Transactions, TransactionsUpdate, User
from access_token import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactionss"])

@router.post("", response_model=TransactionsRead, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: TransactionsCreate, session: SessionDep, current_user: User = Depends(get_current_user)):
    new_tx = Transactions(**transaction.model_dump(), owner_id=current_user.id)

    session.add(new_tx)
    session.commit()
    session.refresh(new_tx)
    return new_tx

@router.get("", response_model=list[TransactionsRead])
def get_transactions(session: SessionDep, current_user: User = Depends(get_current_user)):
    statement = select(Transactions).where(Transactions.owner_id == current_user.id)
    transactions = session.exec(statement).all()
    return transactions

@router.get("/{transaction_id}", response_model=TransactionsRead)
def get_transaction_by_id(transaction_id: int, session: SessionDep, current_user: User = Depends(get_current_user)):
    transaction = session.exec(select(Transactions).where(transaction_id == Transactions.id, Transactions.owner_id == current_user.id)).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transactions not found")
    return transaction

@router.put("/{transaction_id}", response_model=TransactionsRead, status_code=status.HTTP_202_ACCEPTED)
def update_transaction(transaction_id: int, transaction_update: TransactionsUpdate, session: SessionDep, current_user: User = Depends(get_current_user)):
    updated_tx = session.exec(select(Transactions).where(Transactions.id == transaction_id, Transactions.owner_id == current_user.id)).first()
    if not updated_tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transactions not found")
    
    transaction_data = transaction_update.model_dump(exclude_unset=True)
    updated_tx.sqlmodel_update(transaction_data)

    session.add(updated_tx)
    session.commit()
    session.refresh(updated_tx)
    return updated_tx

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, session: SessionDep, current_user: User = Depends(get_current_user)):
    transaction = session.exec(select(Transactions).where(Transactions.id == transaction_id, Transactions.owner_id == current_user.id)).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Transactions not found')
    session.delete(transaction)
    session.commit()
    return None