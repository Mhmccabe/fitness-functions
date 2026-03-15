'use strict';

/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    // ── Rule 1: Controllers must not import from repositories ──────────────────
    {
      name: 'no-repository-in-controller',
      severity: 'error',
      comment:
        'Controllers must delegate to services, not access repositories directly. ' +
        'Direct repository access in a controller bypasses business logic.',
      from: { path: 'src/controllers/' },
      to: { path: 'src/repositories/' },
    },

    // ── Rule 2: Routes must not skip the controller layer ──────────────────────
    {
      name: 'no-service-in-routes',
      severity: 'error',
      comment:
        'Routes must call controllers only. Importing services directly from routes ' +
        'skips the controller layer and breaks the 4-tier hierarchy.',
      from: { path: 'src/routes/' },
      to: { path: 'src/services/' },
    },

    // ── Rule 3: Routes must not access repositories ────────────────────────────
    {
      name: 'no-repository-in-routes',
      severity: 'error',
      comment: 'Routes must not import from repositories — two layers too deep.',
      from: { path: 'src/routes/' },
      to: { path: 'src/repositories/' },
    },

    // ── Rule 4: Services must not import controllers ───────────────────────────
    {
      name: 'no-controller-in-service',
      severity: 'error',
      comment:
        'Services must not depend on controllers. ' +
        'Dependency direction: routes → controllers → services → repositories.',
      from: { path: 'src/services/' },
      to: { path: 'src/controllers/' },
    },

    // ── Rule 5: No circular dependencies ──────────────────────────────────────
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'Circular dependencies make the codebase hard to reason about and test.',
      from: {},
      to: { circular: true },
    },

    // ── Rule 6: Production code must not import from bad/ ─────────────────────
    {
      name: 'no-bad-imports-in-production',
      severity: 'error',
      comment: 'The bad/ directory contains intentional violation examples — not for import.',
      from: { path: '^src/(?!bad/)' },
      to: { path: 'src/bad/' },
    },
  ],

  options: {
    doNotFollow: {
      path: 'node_modules',
    },
    moduleSystems: ['cjs'],
    outputType: 'err',
  },
};
