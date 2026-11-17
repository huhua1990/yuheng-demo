import type { App } from 'vue'
import type { Router } from 'vue-router'

export function setupCompletePlatform(app: App, context: unknown, router: Router, views: Record<string, unknown>): Promise<void>
