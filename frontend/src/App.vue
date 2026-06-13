<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ============ 全局移动端响应式样式 ============ */

/* 小屏幕：768px 以下（手机） */
@media (max-width: 768px) {
  /* 侧边栏变为底部导航 */
  .dashboard {
    flex-direction: column !important;
    min-height: auto !important;
  }

  .sidebar {
    width: 100% !important;
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 1000 !important;
    flex-direction: row !important;
    align-items: center !important;
    padding: 4px 0 !important;
    height: auto !important;
    min-height: auto !important;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.15) !important;
  }

  .sidebar .logo {
    display: none !important;
  }

  .sidebar .nav-menu {
    display: flex !important;
    flex-direction: row !important;
    flex: 1 !important;
    padding: 0 !important;
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
  }

  .sidebar .nav-item {
    flex: 1 !important;
    padding: 8px 4px !important;
    text-align: center !important;
    font-size: 11px !important;
    white-space: nowrap !important;
    min-width: 50px !important;
  }

  .sidebar .lang-switch,
  .sidebar .user-info {
    display: none !important;
  }

  /* 主内容区域 */
  .main-content {
    padding: 12px !important;
    padding-bottom: 70px !important; /* 给底部导航留空间 */
    width: 100% !important;
    min-width: 0 !important;
  }

  /* 页面标题 */
  .page-header {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 12px !important;
    margin-bottom: 16px !important;
  }

  .page-header h1 {
    font-size: 20px !important;
  }

  .header-actions {
    flex-wrap: wrap !important;
    width: 100% !important;
    gap: 8px !important;
  }

  .header-actions .el-input {
    width: 100% !important;
  }

  /* 统计卡片网格 */
  .stats-grid {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 12px !important;
    margin-bottom: 20px !important;
  }

  .stat-card {
    padding: 16px !important;
  }

  .stat-icon {
    font-size: 24px !important;
  }

  .stat-value {
    font-size: 20px !important;
  }

  /* 表格横向滚动 */
  .el-table {
    font-size: 12px !important;
  }

  .el-table .el-table__body-wrapper {
    overflow-x: auto !important;
  }

  /* 站点分组 */
  .site-group-header {
    padding: 12px 14px !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 8px !important;
  }

  .site-group-title {
    flex-wrap: wrap !important;
    gap: 6px !important;
  }

  .site-name {
    font-size: 14px !important;
  }

  /* 对话框 */
  .el-dialog {
    width: 92% !important;
    margin: 0 auto !important;
    margin-top: 20px !important;
  }

  /* 表单 */
  .el-form-item__label {
    font-size: 13px !important;
  }

  /* 空状态 */
  .empty-state {
    padding: 40px 16px !important;
  }

  .empty-icon {
    font-size: 36px !important;
  }

  /* 隐藏一些桌面端元素 */
  .recent-section .el-table-column:first-child,
  .site-group-body .el-table-column:first-child {
    min-width: 50px !important;
  }
}

/* 超小屏幕：480px 以下 */
@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr !important;
    gap: 8px !important;
  }

  .stat-card {
    padding: 12px !important;
  }

  .stat-value {
    font-size: 18px !important;
  }

  .stat-label {
    font-size: 12px !important;
  }

  .page-header h1 {
    font-size: 18px !important;
  }

  .sidebar .nav-item {
    font-size: 10px !important;
    padding: 6px 2px !important;
  }
}

/* 平板：769px - 1024px */
@media (min-width: 769px) and (max-width: 1024px) {
  .sidebar {
    width: 200px !important;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr) !important;
  }

  .main-content {
    padding: 16px !important;
  }
}
</style>
