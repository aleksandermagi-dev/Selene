# Great Library Tendril Adapter

Status: implemented, disabled by default, no activation change.

Selene may use the Great Library only as attributed external reference material
or to submit a proposal for Aleks's review. Retrieval is not identity, memory,
training, or activation.

Required local environment:

```text
SELENE_LIBRARY_TENDRIL_ENABLED=true
GLOA_TENDRIL_URL=http://127.0.0.1:47832
GLOA_TENDRIL_TOKEN=<Selene token issued once by Aleks in the Library desktop>
```

The adapter accepts only `observe` and `propose`. It has no publication,
reclassification, deletion, memory-write, archive-import, or `act` method. The
Library desktop must be running. The token belongs to Selene's interface only
and must not be committed.
