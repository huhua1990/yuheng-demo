import type { MemberIntegrationComponents } from './integration-components'
import * as WalletApi from '@/api/pay/wallet/balance'
import UserBalanceUpdateForm from './user/components/UserBalanceUpdateForm.vue'
import UserBalanceList from './user/detail/UserBalanceList.vue'
import UserFavoriteList from './user/detail/UserFavoriteList.vue'
import UserOrderList from './user/detail/UserOrderList.vue'
import UserAfterSaleList from './user/detail/UserAftersaleList.vue'
import UserBrokerageList from './user/detail/UserBrokerageList.vue'
import UserCouponList from './user/detail/UserCouponList.vue'
import { CouponSendForm } from '@/views/mall/promotion/coupon/components'

export const memberIntegrationComponents: MemberIntegrationComponents = {
  pay: {
    loadWallet: (userId) => WalletApi.getWallet({ userId }),
    balanceList: UserBalanceList,
    balanceUpdateForm: UserBalanceUpdateForm
  },
  product: { favoriteList: UserFavoriteList },
  trade: {
    orderList: UserOrderList,
    afterSaleList: UserAfterSaleList,
    brokerageList: UserBrokerageList
  },
  promotion: { couponList: UserCouponList, couponSendForm: CouponSendForm }
}
