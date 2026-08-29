# Agent Instructions

instruction_contract_version: 3

## Task Routes

<!-- ew:route id="provider-change" triggers="providers/**" owners="docs/providers.md" guards="test:provider-contract" -->
| provider-change | `providers/**` | `docs/providers.md` | provider contract tests |

<!-- ew:route id="ui-change" triggers="frontend/**" owners="docs/ui.md" guards="harness:rendered-ui" -->
| ui-change | `frontend/**` | `docs/ui.md` | rendered UI harness |

<!-- ew:route id="release-change" triggers="release/**" owners="docs/operations.md" guards="release_gate:release-check" -->
| release-change | `release/**` | `docs/operations.md` | release gate |

<!-- ew:route id="browser-change" triggers="browser/**|renderers/**" owners="docs/browser.md" guards="lint:source-shape" -->
| browser-change | browser/refactor code | `docs/browser.md` | source-shape lint |

<!-- ew:route id="repository-change" triggers="**" owners="docs/engineering/project_principles.md" guards="manual_review:run repository gates mapped by the owner" -->
| repository-change | any repository change | `docs/engineering/project_principles.md` | repository gates |

<!-- ew:route id="long-running-execution" triggers="long-running commands|builds|tests|polling" owners="docs/engineering/project_principles.md" guards="manual_review:verify completion evidence deadline bounded output and task-owned cleanup" -->
| long-running-execution | long-running local work | `docs/engineering/project_principles.md` | completion evidence review |
