# ADO Cli Tool

### TODO
- [ ] Fix colour on Powershell  
- [ ] Input Validation - Yaml Validate & Input Arg Validation (username must be email address etc..)    
- [ ] Support Acceptance Criteria Saving  
- [ ] Support Tag Based Search  
- [ ] Support Work Item List caching - Store ID->Property data locally for list - Only refresh previously captured details with `--force` or after set timeframe    
- [X] Close Work Items and State Changes with `ado close`  
- [X] Display Parent/Child Hierarchy with `ado list`  
- [X] Global Log Level / Verbosity Flags  
- [X] Setuptools & Distribution DOcs
- [X] Show Iteration with `ado list`  
- [X] Support Create with Iteration
- [X] Support OS Agnostic `ado open $ID` command - currently supports Windows Only  
- [X] Support Organization/Project argument changes for every command - currently from `.ado-config.yml` only   
- [X] Support Variable Work Item Types  
- [X] Support coloured output  
- [X] Support for Work Item state changes `ado move $ID $state $comment`  