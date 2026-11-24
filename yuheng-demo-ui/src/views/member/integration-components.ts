import type { Component } from 'vue'

export interface MemberWallet {
  id?: number
  userId?: number
  userType?: number
  balance?: number
  totalExpense?: number
  totalRecharge?: number
  freezePrice?: number
}

export interface MemberIntegrationComponents {
  pay?: {
    loadWallet: (userId: number) => Promise<MemberWallet | undefined>
    balanceList?: Component
    balanceUpdateForm?: Component
  }
  product?: {
    favoriteList?: Component
  }
  trade?: {
    orderList?: Component
    afterSaleList?: Component
    brokerageList?: Component
  }
  promotion?: {
    couponList?: Component
    couponSendForm?: Component
  }
}
