from sevdesk.base.basecontroller import BaseController
from sevdesk.models.createprivatetransactionrule import CreatePrivateTransactionRule
from sevdesk.models.privatetransactionruleresponse import PrivateTransactionRuleResponse

class PrivateTransactionRuleController(BaseController):

    @BaseController.get("/PrivateTransactionRule")
    def listPrivateTransactionRules(self) -> list[PrivateTransactionRuleResponse]:
        """List existing rules"""
        return (yield)

    @BaseController.post("/PrivateTransactionRule")
    def createPrivateTransactionRule(self, body: CreatePrivateTransactionRule) -> PrivateTransactionRuleResponse:
        """Create a new rule"""
        return (yield)

    @BaseController.delete("/PrivateTransactionRule/{id}")
    def deletePrivateTransactionRule(self, id_: int):
        """Delete the rule by id"""
        return (yield)

