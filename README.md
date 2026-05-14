# 📘 OmniBioAI Policy Engine

**Policy Engine is the authorization brain of the OmniBioAI ecosystem.**
It evaluates *who can do what*, *on which resource*, under *what conditions*.

It enforces RBAC + ABAC rules across distributed systems like TES, Workbench, Studio, and future HPC services.

---

## 🧠 What this service does

The Policy Engine answers a single question:

> **"Is this user allowed to perform this action on this resource?"**

It evaluates:

* Role-Based Access Control (RBAC)
* Attribute-Based Access Control (ABAC)
* Custom business rules
* HPC constraints (GPU / cluster / quota)
* Dataset-level access policies

---

## 🧬 Architecture Role

```
                 ┌────────────────────┐
                 │  Auth Service      │
                 │  (Identity)        │
                 └─────────┬──────────┘
                           │
                 ┌─────────▼──────────┐
                 │ IAM Client         │
                 │ (Fast cache layer) │
                 └─────────┬──────────┘
                           │
                 ┌─────────▼──────────┐
                 │ Policy Engine      │
                 │ (Decision layer)   │
                 └─────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
      TES             Workbench           Studio
```

---

## ⚙️ Core Features

### 🔐 RBAC (Role-Based Access Control)

* Admin, researcher, data scientist roles
* Action-level restrictions

### 🧠 ABAC (Attribute-Based Access Control)

* GPU usage restrictions
* HPC node access control
* Dataset sensitivity rules

### 📜 Rule Engine

* Domain-specific policies
* Bioinformatics dataset protection rules
* Model registry immutability rules

---

## 🚀 API Overview

### Evaluate Policy

```http
POST /policy/evaluate
```

---

### Request

```json
{
  "user_id": "123",
  "roles": ["researcher"],
  "permissions": [],
  "action": "tes.run_workflow",
  "resource": "rnaseq_pipeline",
  "context": {
    "gpu_required": true,
    "node": "hpc"
  }
}
```

---

### Response

```json
{
  "allowed": true,
  "reason": "access granted",
  "policy_source": "ALL_PASSED"
}
```

---

## 🧠 Policy Evaluation Flow

1. **RBAC check**

   * Validates user roles

2. **ABAC check**

   * Evaluates runtime context (GPU, HPC, etc.)

3. **Rule engine**

   * Applies domain-specific constraints

4. **Decision returned**

   * ALLOW / DENY + reason

---

## 🧩 Integration Points

This service is used by:

* TES (workflow execution authorization)
* Workbench (dataset access control)
* Studio (pipeline execution control)
* IAM Client (future cached policy decisions)

---

## ⚡ Design Philosophy

* Stateless API
* Deterministic decisions
* Fast evaluation (<10ms target)
* Extendable rule system
* HPC-aware security model

---

## 🧪 Example Use Cases

### 1. Prevent GPU abuse

* Only GPU-enabled users can run ML pipelines

### 2. Protect genomic datasets

* Human genome datasets require elevated permissions

### 3. Control HPC usage

* Cluster-specific access control

### 4. Secure model registry

* Prevent deletion of production models

---

## 🔮 Future Enhancements

* Redis caching for policy decisions
* OPA (Open Policy Agent) integration
* Policy versioning system
* Org-level multi-tenancy
* Audit logging integration

---

## 🛠 Tech Stack

* FastAPI
* Python 3.11+
* Pydantic models
* Pluggable RBAC/ABAC engine
* Optional Redis caching (future)

---

## 🧬 Why this exists

In a distributed bioinformatics + AI system, you need:

* Compute governance
* Data protection
* Reproducibility control
* Multi-user safety

This service ensures **every action is explicitly authorized**.

---

## 🧠 Summary

The Policy Engine is the **decision-making layer** of OmniBioAI.

If Auth says:

> “Who are you?”

Then Policy Engine says:

> “What are you allowed to do?”

