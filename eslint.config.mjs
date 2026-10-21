import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';
import tseslint from 'typescript-eslint';
import importPlugin from 'eslint-plugin-import';
import checkFile from 'eslint-plugin-check-file';
import prettierConfig from 'eslint-config-prettier';

// ── 아키텍처 공통 패턴 (frontend:architecture 스킬 규칙) ──────────

/** Slice 내부 직접 접근 차단 */
const sliceInternalPatterns = [
  { group: ['@shared/api/*/*'], message: '@shared/api/[domain] entrypoint를 통해 접근하세요.' },
  { group: ['@pages/*/*'], message: '@pages/[page] entrypoint를 통해 접근하세요.' },
  { group: ['@widgets/*/*'], message: '@widgets/[widget] entrypoint를 통해 접근하세요.' },
  { group: ['@features/*/*'], message: '@features/[feature] entrypoint를 통해 접근하세요.' },
  { group: ['@entities/*/*'], message: '@entities/[entity] entrypoint를 통해 접근하세요.' },
];

/** 상대경로로 다른 레이어 접근 차단 */
const noRelativeCrossLayerPattern = {
  group: [
    '../**/app/**', '../**/pages/**', '../**/shared/**',
    '../**/widgets/**', '../**/features/**', '../**/entities/**',
  ],
  message: '다른 레이어는 path alias를 사용하세요. 상대경로는 레이어 내부에서만 허용됩니다.',
};

const basePatterns = [...sliceInternalPatterns, noRelativeCrossLayerPattern];

/** 역방향 import 차단 패턴 생성 */
function blockLayers(...layers) {
  return [{
    group: layers.flatMap((l) => [`@${l}`, `@${l}/*`]),
    message: `이 레이어에서 ${layers.join(', ')} 레이어를 import할 수 없습니다.`,
  }];
}

/** 같은 레이어 alias 차단 패턴 생성 (자기 Slice·sibling Slice 모두) */
function blockSelfAlias(layer) {
  return [{
    group: [`@${layer}`, `@${layer}/*`],
    message: '같은 레이어 내부에서는 상대경로를 사용하세요. path alias는 다른 레이어 import 전용입니다.',
  }];
}

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  ...tseslint.configs.recommended,

  // ── 아키텍처 기본 규칙 (특정 레이어에 속하지 않는 파일) ────────
  {
    plugins: { import: importPlugin, 'check-file': checkFile },
    rules: {
      'no-restricted-imports': ['error', { patterns: basePatterns }],
      '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],
      'import/no-default-export': 'error',
      'import/no-cycle': ['error', { maxDepth: Infinity }],
      'check-file/filename-naming-convention': ['error', {
        '**/*.{ts,tsx,js,jsx}': 'KEBAB_CASE',
      }, {
        ignoreMiddleExtensions: true,
      }],
    },
  },

  // ── Default Export 예외: 프레임워크가 요구하는 파일 ────────────
  {
    files: [
      // Next.js App Router — UI 컴포넌트
      'app/**/page.tsx', 'app/**/layout.tsx', 'app/**/loading.tsx',
      'app/**/error.tsx', 'app/**/not-found.tsx', 'app/**/template.tsx',
      'app/**/default.tsx', 'app/global-error.tsx',
      // Next.js App Router — 메타데이터 생성 파일
      'app/**/icon.tsx', 'app/**/apple-icon.tsx',
      'app/**/opengraph-image.tsx', 'app/**/twitter-image.tsx',
      'app/manifest.ts', 'app/sitemap.ts', 'app/robots.ts',
      // Next.js Pages Router
      'pages/**/*.tsx',
      // 루트 설정 파일 — 각 도구가 default export를 요구
      'eslint.config.mjs', 'next.config.ts', 'next.config.js', 'postcss.config.mjs', 'postcss.config.js',
    ],
    rules: {
      'import/no-default-export': 'off',
    },
  },

  // ── API route는 아키텍처 레이어를 import할 수 없다 ─────────────
  {
    files: ['app/api/**/*.{ts,tsx,js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          {
            group: [
              '@app', '@app/*', '@pages', '@pages/*', '@shared', '@shared/*',
              '@widgets', '@widgets/*', '@features', '@features/*', '@entities', '@entities/*',
            ],
            message: 'API route는 아키텍처 레이어를 import할 수 없습니다. 자체적으로 로직을 완결하세요.',
          },
        ],
      }],
    },
  },

  // ── 레이어별 import 방향 규칙 ────────────────────────────────

  // shared: 모든 상위 레이어 import 금지 (자기 alias는 허용 — segment 분산 구조)
  {
    files: ['src/shared/**/*.{ts,tsx,js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          ...basePatterns,
          ...blockLayers('app', 'pages', 'widgets', 'features', 'entities'),
        ],
      }],
    },
  },

  // entities: shared만 import 가능 + 자기 alias 차단
  {
    files: ['src/entities/**/*.{ts,tsx,js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          ...basePatterns,
          ...blockLayers('app', 'pages', 'widgets', 'features'),
          ...blockSelfAlias('entities'),
        ],
      }],
    },
  },

  // features: entities, shared만 import 가능 + 자기 alias 차단
  {
    files: ['src/features/**/*.{ts,tsx,js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          ...basePatterns,
          ...blockLayers('app', 'pages', 'widgets'),
          ...blockSelfAlias('features'),
        ],
      }],
    },
  },

  // widgets: features, entities, shared만 import 가능 + 자기 alias 차단
  {
    files: ['src/widgets/**/*.{ts,tsx,js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          ...basePatterns,
          ...blockLayers('app', 'pages'),
          ...blockSelfAlias('widgets'),
        ],
      }],
    },
  },

  // pages: app import 금지 + 자기 alias 차단
  {
    files: ['src/pages/**/*.{ts,tsx,js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          ...basePatterns,
          ...blockLayers('app'),
          ...blockSelfAlias('pages'),
        ],
      }],
    },
  },

  // app: 모든 레이어 import 가능 + 자기 alias 차단
  {
    files: ['src/app/**/*.{ts,tsx,js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          ...basePatterns,
          ...blockSelfAlias('app'),
        ],
      }],
    },
  },

  // Prettier와 충돌하는 스타일 규칙 비활성화 (항상 마지막)
  prettierConfig,

  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    '.next/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
  ]),
]);

export default eslintConfig;
