# Agent Instructions

instruction_contract_version: 1

## Task Routes

<!-- ew:route id="provider-change" triggers="providers/**" owners="docs/providers.md" guards="test:provider-contract" -->
| provider-change | `providers/**` | `docs/providers.md` | provider contract tests |

<!-- ew:route id="ui-change" triggers="frontend/**" owners="docs/ui.md" guards="harness:rendered-ui" -->
| ui-change | `frontend/**` | `docs/ui.md` | rendered UI harness |

<!-- ew:route id="release-change" triggers="release/**" owners="docs/operations.md" guards="release_gate:release-check" -->
| release-change | `release/**` | `docs/operations.md` | release gate |

<!-- ew:route id="browser-change" triggers="browser/**|renderers/**" owners="docs/browser.md" guards="lint:source-shape" -->
| browser-change | browser/refactor code | `docs/browser.md` | source-shape lint |
