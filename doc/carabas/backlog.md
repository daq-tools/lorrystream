# Carabas Backlog

## Iteration +1
- [x] Improve type mapping
- [x] Generalize CDC event -> SQL translator
- [ ] Only optionally display debug output of Docker build process,
  [ ] when using `--verbose`.
- [ ] Bring back "Zip" use, for interactive hacking
- [ ] Distill into a Lambda variant
- [ ] Automation!
  - [ ] DDL: CREATE TABLE <tablename> (data OBJECT(DYNAMIC));
  - [ ] Wrap KCL launcher into manager component

## Iteration +2
- [ ] Performance improvements (simdjson?)
- [ ] Use SQLAlchemy for generating and submitting SQL statement
- [ ] Improve efficiency by using bulk operations when applicable
- [ ] is in UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS state and can not be updated
- [ ] is in ROLLBACK_COMPLETE state and can not be updated.
- [ ] Cannot create a publicly accessible DBInstance. The specified VPC has no
  internet gateway attached.Update the VPC and then try again
