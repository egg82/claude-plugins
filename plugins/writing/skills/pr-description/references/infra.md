# Infra / GitOps changes

Load for manifests, Terraform or Ansible changes.

**Infra / GitOps changes** (manifests, Terraform, Ansible) need less prose and more of the conditional
sections: name the blast radius (which site, cluster or service), let **Verified** show what the
dry run, plan or rendered diff produced, and always give **After merge** (the live check) and
**Rollback** when anything stateful moves.
