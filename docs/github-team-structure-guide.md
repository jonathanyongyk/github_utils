# GitHub Enterprise Cloud — Org Team Structure Guide
## Regular Members + TechLead Setup

> **Version:** 1.1
> **Date:** 2026-03-30
> **Audience:** GitHub Org Admins, Platform Engineers, Migration Teams

---

## Table of Contents

- [GitHub Enterprise Cloud — Org Team Structure Guide](#github-enterprise-cloud--org-team-structure-guide)
  - [Regular Members + TechLead Setup](#regular-members--techlead-setup)
  - [Table of Contents](#table-of-contents)
  - [1. Overview](#1-overview)
  - [2. Scenario](#2-scenario)
    - [2.1 Background](#21-background)
    - [2.2 The Requirement](#22-the-requirement)
    - [2.3 Why This Cannot Be Done With a Single Team](#23-why-this-cannot-be-done-with-a-single-team)
    - [2.4 Illustration of the Problem](#24-illustration-of-the-problem)
    - [2.5 How Permissions Flow](#25-how-permissions-flow)
    - [2.6 What TechLeads Can Do That Regular Members Cannot](#26-what-techleads-can-do-that-regular-members-cannot)
      - [On the Team](#on-the-team)
      - [On the Repositories](#on-the-repositories)
    - [2.7 EMU Consideration for This Scenario](#27-emu-consideration-for-this-scenario)
  - [3. Role Concepts](#3-role-concepts)
  - [4. Recommended Structure: Nested Teams](#4-recommended-structure-nested-teams)
    - [Why This Works](#why-this-works)
  - [5. Team Role Capabilities](#5-team-role-capabilities)
  - [6. Repository Role Comparison](#6-repository-role-comparison)
  - [7. Step-by-Step Setup Guide](#7-step-by-step-setup-guide)
    - [Step 1 — Create the Parent Team](#step-1--create-the-parent-team)
    - [Step 2 — Add All Repos to the Parent Team with `Write` Role](#step-2--add-all-repos-to-the-parent-team-with-write-role)
    - [Step 3 — Add Regular Members to the Parent Team](#step-3--add-regular-members-to-the-parent-team)
    - [Step 4 — Create the Child Team for TechLeads](#step-4--create-the-child-team-for-techleads)
    - [Step 5 — Override Repo Role on Child Team to `Admin`](#step-5--override-repo-role-on-child-team-to-admin)
    - [Step 6 — Add TechLeads to Child Team as Maintainers](#step-6--add-techleads-to-child-team-as-maintainers)
  - [8. Final State Verification](#8-final-state-verification)
    - [Verification Checklist](#verification-checklist)
  - [9. EMU-Specific Watch-Outs](#9-emu-specific-watch-outs)
  - [10. Key Watch-Outs \& Gotchas](#10-key-watch-outs--gotchas)
  - [11. Admin vs Maintain — Which Should TechLeads Use?](#11-admin-vs-maintain--which-should-techleads-use)
  - [12. When Adding a New Repo to the Team](#12-when-adding-a-new-repo-to-the-team)
  - [13. When Adding a New Member to the Team](#13-when-adding-a-new-member-to-the-team)
  - [14. When Adding a New Product](#14-when-adding-a-new-product)
  - [15. References](#15-references)

---

## 1. Overview

This guide documents the recommended GitHub team structure for organizations migrating from
Bitbucket/Azure DevOps to GitHub Enterprise Cloud, specifically for teams that have:

- **Regular members** — developers who need standard push/pull/PR access (`Write`)
- **TechLeads** — senior engineers who need full repo management access (`Admin` or `Maintain`)
  and the ability to manage team membership

---

> **Note:** Although Bitbucket and Azure DevOps is mentioned in this doc as the source of DevOps tool to migrate from,
> the concept apply to any DevOps tool which has the concept of project.
> 
> The concept of project allude as a logical container for a set of assets (such as soure code, people, work items, CI/CD) 
> which contribute to a working system or application.
> 
> Wherever Bitbucket or Azure DevOps is mentioned, it can be replaced with any similar concept in other DevOps tools.

## 2. Scenario

### 2.1 Background

During migration from Bitbucket to GitHub Enterprise Cloud, a common requirement is to
replicate an existing team access model where:

- A **single team** owns a collection of repositories
- **Regular developers** need day-to-day development access (clone, push, pull, raise PRs)
- **TechLeads** need elevated access to manage the repositories (branch protections, webhooks,
  settings) and the team membership itself

This scenario is typical for product or platform engineering teams where TechLeads are responsible
for both the technical direction and the operational governance of the team's repositories.

> **Note:** The scenario described here is hypothetical. It does not prescribe how every team
> must be set up, but serves as a reference model to help admins think through team structure
> and repository access design.

### 2.2 The Requirement

> *"I created an Org team. Within the team, there are multiple repos. There are two groups of
> members. One is regular members who can only perform normal operations like pull, push, PR on
> repos. Another group is called TechLead. TechLead should have team maintainer role and admin
> role to all repos in the team."*

Translated into GitHub concepts:

| Requirement | GitHub Equivalent |
|---|---|
| One Org team | **Parent Team** (e.g., `backend-devs`) |
| Multiple repos in the team | Repos assigned to the parent team |
| Regular members — pull, push, PR | Team repo permission: **`Write`** |
| TechLeads — admin to all repos | Team repo permission: **`Admin`** (or `Maintain`) |
| TechLeads — manage the team | Team membership role: **`Maintainer`** |

### 2.3 Why This Cannot Be Done With a Single Team

A single GitHub team can only have **one repository permission level** assigned per repo
(e.g., `Write` OR `Admin` — not both at the same time for different members).

All members of a team inherit the **same** repository role. There is no concept of
"this member gets Write, that member gets Admin" within a single team.

Therefore, to support two different groups with different repo access levels, you need
**two teams** — which is where the **Nested Teams (Parent + Child)** model comes in.

### 2.4 Illustration of the Problem

```
❌ WRONG — Single team, cannot have two different repo permission levels:

  Team: backend-devs  (repo access: ???)
  ├── Alice (dev)     → needs Write
  ├── Bob   (dev)     → needs Write
  ├── Carol (TL)      → needs Admin   ← CONFLICT
  └── Dave  (TL)      → needs Admin   ← CONFLICT
```

```
✅ CORRECT — Nested teams, each with their own repo permission level:

  Team: backend-devs  (repo access: Write)
  ├── Alice (dev)     → gets Write  ✅
  ├── Bob   (dev)     → gets Write  ✅
  │
  └── Team: backend-devs-techleads  (repo access: Admin)  ← child team
      ├── Carol (TL)  → gets Admin  ✅
      └── Dave  (TL)  → gets Admin  ✅
```

### 2.5 How Permissions Flow

GitHub team permissions are **additive** and **hierarchical**:

1. The **parent team** (`backend-devs`) is assigned `Write` access to all repos
2. The **child team** (`backend-devs-techleads`) is **nested under** the parent
3. The child team **inherits** the parent's repo list automatically
4. The child team's repo permission is **overridden to `Admin`** — which takes precedence
   over the inherited `Write`
5. TechLeads are members of **both** teams — they get `Admin` (the higher permission wins)
6. TechLeads are assigned the **Team Maintainer** role on the child team — giving them
   the ability to manage team membership

```
Permission Flow Diagram:

  backend-devs (parent)
  │  └── Repos: repo-one, repo-two, repo-three
  │       └── Permission: Write
  │
  └── backend-devs-techleads (child)
       └── Repos: repo-one, repo-two, repo-three  ← INHERITED from parent
            └── Permission: Admin  ← OVERRIDES inherited Write
```

### 2.6 What TechLeads Can Do That Regular Members Cannot

#### On the Team

| Action | Regular Member | TechLead (Team Maintainer) |
|---|---|---|
| View team members | ✅ | ✅ |
| Add/remove members from the team | ❌ | ✅ |
| Promote a member to Team Maintainer | ❌ | ✅ |
| Change team name and description | ❌ | ✅ |
| Manage code review assignment settings | ❌ | ✅ |
| Manage scheduled PR reminders | ❌ | ✅ |

#### On the Repositories

| Action | Regular Member (`Write`) | TechLead (`Admin`) |
|---|---|---|
| Clone, pull, push, raise PRs | ✅ | ✅ |
| Merge pull requests | ✅ | ✅ |
| Manage issues and labels | ✅ | ✅ |
| Manage branch protections and rulesets | ❌ | ✅ |
| Manage webhooks and integrations | ❌ | ✅ |
| Manage GitHub Pages | ❌ | ✅ |
| Bypass push restrictions on protected branches | ❌ | ✅ |
| Change repository visibility | ❌ | ✅ |
| Delete or transfer the repository | ❌ | ✅ |
| Archive the repository | ❌ | ✅ |
| Manage team and collaborator access to the repo | ❌ | ✅ |

> ⚠️ **Consideration:** If TechLeads should **not** be able to delete or transfer repositories,
> use **`Maintain`** instead of `Admin` for the child team. See
> [Section 11](#11-admin-vs-maintain--which-should-techleads-use) for a full comparison.

### 2.7 EMU Consideration for This Scenario

In an **Enterprise Managed Users (EMU)** environment, if your teams are linked to
an **Identity Provider (IdP)** group (Entra ID / Okta):

- Team membership is **fully managed by the IdP** — no manual add/remove in GitHub UI
- The **Team Maintainer** role cannot be set via the GitHub UI for IdP-linked teams
- You must create **two separate IdP groups**:
  - One group for regular developers → synced to `backend-devs`
  - One group for TechLeads → synced to `backend-devs-techleads`
- Ownership and lifecycle of these groups is managed in your IdP, not in GitHub

```
EMU + IdP Setup:

  Entra ID / Okta
  ├── Group: "github-backend-devs"        → synced to → Team: backend-devs
  └── Group: "github-backend-techleads"   → synced to → Team: backend-devs-techleads
```

---

## 3. Role Concepts

There are **two separate and distinct role systems** in GitHub that are often confused:

| Layer | Roles | Controls |
|---|---|---|
| **Team Membership Role** | `Member` vs `Maintainer` | What you can do **to the team itself** |
| **Repository Role** | `Read`, `Triage`, `Write`, `Maintain`, `Admin` | What you can do **inside a repository** |

> ⚠️ **Critical:** The `Member` and `Maintainer` team roles do **NOT** grant different repository
> access levels. Both roles inherit the **same repository access** from the team. The difference
> is purely about managing the **team itself**.

---

## 4. Recommended Structure: Nested Teams

```
ORGANIZATION
│
└── 🟦 Team: "backend-devs"  (PARENT TEAM)
    │   Members: all developers (regular members)
    │   Repo role: Write  ← all repos assigned here
    │   Team membership role: Member
    │
    └── 🟥 Team: "backend-devs-techleads"  (CHILD TEAM)
            Members: TechLeads only
            Repo role: Admin  ← OVERRIDES parent's Write
            Team membership role: Maintainer
```

### Why This Works

| Benefit | Detail |
|---|---|
| Child teams inherit parent repo access | TechLeads automatically get access to all repos the parent has |
| Child team Admin overrides parent Write | TechLeads get Admin; Devs get Write — on the same repos |
| Adding a new repo to parent is enough | TechLeads automatically get Admin on new repos (after override) |
| Clean separation of concerns | Team management and repo access are independently controllable |

---

## 5. Team Role Capabilities

| Capability | Team Member | Team Maintainer |
|---|---|---|
| **Team Management** | | |
| View team members | ✅ | ✅ |
| Add members to team | ❌ | ✅ |
| Remove members from team | ❌ | ✅ |
| Promote members to Maintainer | ❌ | ✅ |
| Change team name & description | ❌ | ✅ |
| Change team visibility | ❌ | ✅ |
| Set team profile picture | ❌ | ✅ |
| Request add/change parent team | ❌ | ✅ |
| Request add child team | ❌ | ✅ |
| **Repository-Related** | | |
| Access repos (inherits team repo role) | ✅ | ✅ |
| Same repo permissions as the team | ✅ | ✅ |
| Remove team's direct repo access | ❌ | ✅ |
| Reset inherited repo permission | ❌ | ✅ |
| Change the team's repo permission level | ❌ | ❌ (org owner only) |
| Grant team access to new repos | ❌ | ❌ (repo admin/org owner only) |
| **CI/CD & Reviews** | | |
| Manage code review assignment | ❌ | ✅ |
| Manage scheduled PR reminders | ❌ | ✅ |
| **EMU Specific** | | |
| Manually assignable when IdP-linked | ✅ (via IdP) | ❌ (disabled when IdP-linked) |

---

## 6. Repository Role Comparison

| Capability | Read | Triage | Write | Maintain | Admin |
|---|---|---|---|---|---|
| Clone / pull | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create issues | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create PRs | ✅ | ✅ | ✅ | ✅ | ✅ |
| Push code (non-protected branches) | ❌ | ❌ | ✅ | ✅ | ✅ |
| Merge PRs | ❌ | ❌ | ✅ | ✅ | ✅ |
| Manage issues & labels | ❌ | ✅ | ✅ | ✅ | ✅ |
| Manage branch protections | ❌ | ❌ | ❌ | ✅ | ✅ |
| Manage webhooks | ❌ | ❌ | ❌ | ✅ | ✅ |
| Manage GitHub Pages | ❌ | ❌ | ❌ | ✅ | ✅ |
| Push to protected branches (bypass) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Change repo visibility | ❌ | ❌ | ❌ | ❌ | ✅ |
| Delete or transfer repo | ❌ | ❌ | ❌ | ❌ | ✅ |
| Manage team access to repo | ❌ | ❌ | ❌ | ❌ | ✅ |
| Archive repo | ❌ | ❌ | ❌ | ❌ | ✅ |

> 💡 **Recommendation:** If TechLeads only need to manage branch protections and webhooks but
> should NOT delete or transfer repos, use **`Maintain`** instead of `Admin`.

---

## 7. Step-by-Step Setup Guide

### Step 1 — Create the Parent Team

1. Go to your **Org → Teams → New team**
2. Name it: `backend-devs`
3. Set visibility: **Visible**
4. Click **Create team**

### Step 2 — Add All Repos to the Parent Team with `Write` Role

For each repo:
1. Go to **Repo → Settings → Collaborators and teams**
2. Click **Add teams**
3. Search for `backend-devs`
4. Set permission: **`Write`**
5. Click **Add team**

Or via **Team → Repositories tab → Add repository** (repeat per repo)

### Step 3 — Add Regular Members to the Parent Team

1. Go to **Team `backend-devs` → Members → Add a member**
2. Add each regular developer
3. Their team membership role: **`Member`** (default)

### Step 4 — Create the Child Team for TechLeads

1. Go to **Org → Teams → New team**
2. Name it: `backend-devs-techleads`
3. Set **Parent team** → select `backend-devs`
4. Set visibility: **Visible**
5. Click **Create team**

### Step 5 — Override Repo Role on Child Team to `Admin`

The child team inherits `Write` from the parent. Override it to `Admin` per repo:

1. Go to **Repo → Settings → Collaborators and teams**
2. Find `backend-devs-techleads`
3. Change permission: `Write` → **`Admin`**
4. Repeat for all repos

> ⚠️ There is no single "override all inherited repos to Admin" button in the UI.
> Use the provided shell script to do this in bulk.

### Step 6 — Add TechLeads to Child Team as Maintainers

1. Go to **Team `backend-devs-techleads` → Members → Add a member**
2. Add each TechLead
3. Click the **⋮ menu** next to each TechLead
4. Select **Change role → Maintainer**

> ⚠️ **EMU with IdP-linked teams:** Maintainer role assignment via UI is **disabled**.
> Manage roles via your IdP (Entra ID / Okta) group settings instead.

---

## 8. Final State Verification

| Person | Team(s) | Team Role | Effective Repo Access |
|---|---|---|---|
| Alice (dev) | `backend-devs` | Member | ✅ Write (all repos) |
| Bob (dev) | `backend-devs` | Member | ✅ Write (all repos) |
| Carol (TechLead) | `backend-devs` + `backend-devs-techleads` | Maintainer (child) | ✅ Admin (all repos) |
| Dave (TechLead) | `backend-devs` + `backend-devs-techleads` | Maintainer (child) | ✅ Admin (all repos) |

> 💡 TechLeads are members of **both** teams. Their effective repo permission is the
> **highest role assigned** — `Admin` from the child team wins over `Write` from the parent.

### Verification Checklist

- [ ] Regular members can push, pull, and raise PRs on all repos
- [ ] Regular members **cannot** manage branch protections or webhooks
- [ ] TechLeads can push, pull, raise and merge PRs on all repos
- [ ] TechLeads **can** manage branch protections, webhooks, and repo settings
- [ ] TechLeads **can** add and remove members from the `backend-devs-techleads` team
- [ ] TechLeads **cannot** grant new teams access to repos (org owner only)
- [ ] All repos appear under both teams in **Repo → Settings → Collaborators and teams**

---

## 9. EMU-Specific Watch-Outs

| Issue | Detail | Mitigation |
|---|---|---|
| Team Maintainer role disabled for IdP-linked teams | Cannot set via GitHub UI | Manage team leads via IdP group ownership |
| Entra ID does not support nested groups for SCIM | SCIM sync flattens groups | Create two separate flat IdP groups: one for devs, one for TechLeads |
| Okta + Entra ID combo unsupported | Cannot mix IdPs for SSO + SCIM | Use a single IdP for both |
| Users cannot change their own profile | Email, name, username are IdP-managed | Communicate this to users upfront |
| EMU users cannot contribute outside the enterprise | No public repos or external org contributions | Inform devs who maintain open-source work |

---

## 10. Key Watch-Outs & Gotchas

| # | Issue | Detail |
|---|---|---|
| 1 | **Repo override is per-repo** | Must upgrade child team to `Admin` on each repo individually via UI — use script for bulk |
| 2 | **Adding a new repo needs two steps** | Add to parent as `Write`, then override child to `Admin` |
| 3 | **Permissions are additive** | If a TechLead is also added individually to a repo, GitHub uses the highest permission |
| 4 | **Secret team cannot be a parent** | Do not make `backend-devs` a secret team if nesting is required |
| 5 | **Admin is very powerful** | Allows repo deletion and visibility change — consider `Maintain` for most TechLead personas |
| 6 | **Child team repo override does not auto-update** | When parent gets a new repo, child must be re-overridden to `Admin` — automate with scripts or GitHub Actions |

---

## 11. Admin vs Maintain — Which Should TechLeads Use?

| Capability | Write | Maintain | Admin |
|---|---|---|---|
| Push code, create PRs | ✅ | ✅ | ✅ |
| Merge PRs | ✅ | ✅ | ✅ |
| Manage issues & labels | ✅ | ✅ | ✅ |
| Manage branch protections | ❌ | ✅ | ✅ |
| Manage webhooks | ❌ | ✅ | ✅ |
| Manage GitHub Pages | ❌ | ✅ | ✅ |
| Push to protected branches (bypass) | ❌ | ❌ | ✅ |
| Change repo visibility | ❌ | ❌ | ✅ |
| **Delete or transfer repo** | ❌ | ❌ | ✅ |
| Manage team access to repo | ❌ | ❌ | ✅ |
| Archive repo | ❌ | ❌ | ✅ |

> ✅ **Recommended Default:** Use **`Maintain`** for TechLeads unless there is a specific
> business need for repo deletion, visibility changes, or team access management.

---

## 12. When Adding a New Repo to the Team

1. Confirm target teams and required permissions:
  - Parent team (regular members): `push`/`write` equivalent
  - Child TechLead team: `admin` or `maintain` (as per your policy)
2. Add a row in your repo-assignment CSV with the required columns:
  - `org_name`, `team_slug`, `repo_name`, `permission`
3. Add one row per team permission you need (for example one row for parent team, one row for TechLead team).
4. Run the repo assignment script (`src/assign_team_repos.py`):

  ```bash
  python src/assign_team_repos.py --input-csv <path-to-your-csv>
  ```

5. Check the summary output and confirm `Rows failed: 0`.
6. Verify in GitHub UI:
  - **Repo → Settings → Collaborators and teams**
  - Parent team has expected base access
  - TechLead child team has expected elevated access
7. Script reference:
  - `docs/assign_team_repos.md`
8. Without CSV (direct function call):
  - `assign_team_repo_permission(token, org_name, team_slug, repo_name, permission)` from `src/assign_team_repos.py`
  - Use this when you want to assign one team-to-repo permission directly in code without preparing an input CSV.

## 13. When Adding a New Member to the Team

1. Decide which team the user should join:
  - Regular developer → parent team
  - TechLead → child TechLead team (and parent team if your operating model requires both)
2. Set the team role:
  - `member` for regular members
  - `maintainer` for TechLeads who should manage team membership
3. Add a row in member-assignment CSV with the required columns:
  - `org_name`, `team_slug`, `username`, `role`
4. Run the team member assignment script (`src/assign_team_members.py`):

  ```bash
  python src/assign_team_members.py --input-csv <path-to-your-csv>
  ```

5. Check the summary output and confirm `Rows failed: 0`.
6. Verify in GitHub UI:
  - **Org → Teams → <team> → Members**
  - User appears in the expected team with the expected role.
7. Script reference:
  - `docs/assign_team_members.md`
8. Without CSV (direct function call):
  - `assign_user_to_team(token, org_name, team_slug, username, role)` from `src/assign_team_members.py`
  - Use this when you want to add or update one team membership directly in code without preparing an input CSV.

---

## 14. When Adding a New Product

In this guide, **product**, **project**, and **parent org team** are treated as the same unit.
Adding a new product means creating a new parent team (and usually a child TechLead team), then assigning repos and members.

1. Define naming and ownership for the new product:
  - Parent team slug (example: `payments-core`)
  - Child TechLead team slug (example: `payments-core-techleads`)
  - Product repos to assign
  - Initial regular members and TechLeads
2. Create the parent and child teams:
  - Use the team creation script and include parent-child relation for the TechLead team.
  - Script reference: `docs/create_teams.md`
3. Assign product repositories to teams:
  - Parent team gets base access (`push`/`write` equivalent).
  - Child TechLead team gets elevated access (`maintain` or `admin`).
  - Use CSV columns: `org_name`, `team_slug`, `repo_name`, `permission`.
  - Script reference: `docs/assign_team_repos.md`
4. Assign product members to teams:
  - Regular members -> parent team with role `member`.
  - TechLeads -> child TechLead team with role `maintainer`.
  - Use CSV columns: `org_name`, `team_slug`, `username`, `role`.
  - Script reference: `docs/assign_team_members.md`
5. Validate the final state:
  - Parent team has all expected product repos.
  - Child TechLead team has elevated repo access.
  - Membership and roles are correct in both teams.
6. Without CSV (direct function calls):
  - `create_org_team(token, org_name, team_name, privacy='closed', parent_team_id=None, description='')` from `src/create_teams.py`
  - Creates a parent or child team directly via API call; pass `parent_team_id` to create a nested TechLead child team.
  - `assign_team_repo_permission(token, org_name, team_slug, repo_name, permission)` from `src/assign_team_repos.py`
  - Applies repo permission for one team-repo pair directly (for parent `push`/child `maintain` or `admin`) without CSV processing.
  - `assign_user_to_team(token, org_name, team_slug, username, role)` from `src/assign_team_members.py`
  - Adds one user to one team with `member` or `maintainer` role directly without CSV processing.

## 15. References

- [About organization teams — Nested teams](https://docs.github.com/en/enterprise-cloud@latest/organizations/organizing-members-into-teams/about-teams#nested-teams)
- [Managing team access to an organization repository](https://docs.github.com/en/enterprise-cloud@latest/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/managing-team-access-to-an-organization-repository)
- [Assigning the team maintainer role](https://docs.github.com/en/enterprise-cloud@latest/organizations/organizing-members-into-teams/assigning-the-team-maintainer-role-to-a-team-member)
- [Managing team memberships with IdP groups (EMU)](https://docs.github.com/en/enterprise-cloud@latest/admin/identity-and-access-management/using-enterprise-managed-users-for-iam/managing-team-memberships-with-identity-provider-groups)
- [Repository roles for an organization](https://docs.github.com/en/enterprise-cloud@latest/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization)
- [Requesting to add a child team](https://docs.github.com/en/enterprise-cloud@latest/organizations/organizing-members-into-teams/requesting-to-add-a-child-team)