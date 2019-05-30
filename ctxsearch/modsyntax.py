# -*- coding: utf-8 -*-

import re, copy

import urllib.parse

from .actions import ModuleBase

MODULE_NAME = "SyntaxModule"

WORD_SEPARATOR_REGEXP = re.compile(r'[ ,.;!?]+')

class SyntaxModule(ModuleBase):
    def _replace_vars(self, ctx, string):
        p = 0
        result = ""
        while p < len(string):
            if string[p] == "\\":
                result += string[p+1]
                p += 2
            elif string[p] == "$" and p+1 < len(string) and string[p+1] == "{":
                p2 = string.find("}",p+1)
                value = self._eval_expr(ctx, string[p+2: p2], None)
                if isinstance(value,str) or isinstance(value, unicode):
                    result += value
                else:
                    # será um int ou float? e se for uma lista, nao vai funcionar bem...
                    if result:
                        result = str(result) + str(value)
                    else:
                        result = value # nao converte ainda para string...
                p = p2+1
            else:
                result += string[p]
                p+=1
        return result

    def filter_actions(self, ctx, actions):
        return self._eval_list(ctx, actions)

    # grab ou nao?
    def _eval_list(self, ctx, lis):
        result = []
        for element in lis:
            # só posso ter um repeat por hash... porque nao preserva a ordem...
            if "repeat" in element:
                #print("REPEAT")
                match = re.match("(\w+) +\${(\w+)}", element["repeat"])
                if not match:
                    raise Exception("Erro no repeat")
                varname = match.group(1)
                expr = match.group(2)
                #print(varname,expr)
                # TODO verificar se existe no ctx...
                # TODO generalizar a sintaxe...
                values = self._eval_expr(ctx, expr, None)
                if not isinstance(values,list):#listname in ctx:
                    # ignora.
                    # nao dá erro! porque nao pode haver condicoes antes do repeat...
                    continue

                #values = ctx[listname]
                #print("VALUES",values)
                ctx_copy = copy.deepcopy(ctx)
                element_copy = copy.deepcopy(element)
                del element_copy["repeat"]

                for value in values:
                    ctx_copy[varname] = value
                    new = self._eval_hash(ctx_copy, element_copy)
                    if new:
                        result.append(new)

            else:
                new = self._eval_hash(ctx, element)
                if new:
                    result.append(new)

        return result

    # returns a new hash or None if failed condition
    def _eval_hash(self, ctx, action):
        #if self.cfg.DEBUG:
        #print "eval_hash","ctx=",ctx,"action=",action
        result = {}

        for n in action.keys():
            if n == "or":
                # it is a list
                parts = self._eval_list(ctx, action[n])
                if parts:
                    for part in parts:
                        for key in part:
                            result[key] = part[key]
                else:
                    return None

            elif n == "not":
                # ignore params here
                if self._eval_hash(ctx, action[n]) != None:
                    return None

            else:
                if n.find("__") == -1 and not n in ctx:
                    if isinstance(action[n], list):
                        result[n] = self._eval_list(ctx, action[n])
                    else:
                        # str ou unicode? :(
                        # TODO testar yaml com acentos...
                        value = action[n]
                        if isinstance(value, str): # 201905 ignorei isto... nao existe "unicode" em py3??? - or isinstance(value, unicode):
                            # pode ser um int, um float ou outro tipo primitivo suportado pelo yaml...
                            value = self._replace_vars(ctx, value)

                        result[n] = value

                else:
                     # is a condition   
                    if not self._eval_expr(ctx, n, action[n]):
                        return None

        # nota: uma hash vazia nao é o mesmo que None!
        return result

    def _eval_expr(self, obj, expr, arg):
        #if self.cfg.DEBUG:
        #print("eval_expr","obj=",obj,"expr=",expr,"arg=",arg)
        
        final = False

        p = expr.find("__")
        
        if p == -1:
            n = expr
            expr_tail = None
        else:
            n = expr[0:p]
            expr_tail = expr[p+2: ]

        if n == "len":
            obj = len(obj)
        elif n == "quote":
            obj = urllib.parse.quote(obj)
        elif n == "match":
            final = True # sim?? pq?
            obj = re.match(arg, obj)
        elif n == "words":
            obj = len(WORD_SEPARATOR_REGEXP.split(obj.strip()))

        elif n == "gt":
            final = True
            obj = obj > arg
        elif n == "lt":
            final = True
            obj = obj < arg
        elif n == "ge":
            final = True
            obj = obj >= arg
        elif n == "le":
            final = True
            obj = obj <= arg
            # TODO le, ge, eq, ne

        else:
            if isinstance(obj, dict) and n in obj:
                obj = obj[n]
            elif hasattr(obj, n):
                obj = getattr(obj, n)
            else:
                #obj = True
                #final = True
                #pass # ignore?
                obj = None
                # final = True
                #return True #raise Exception("Nao encontro "+n+" em "+obj)

        if final and expr_tail:
            raise Exception("ERE in "+expr_tail)

        if expr_tail:
            return self._eval_expr(obj, expr_tail, arg)
        elif final:
            return obj
        elif arg == None:
            return obj
        else:
            return obj == arg #??
    
if __name__ == "__main__":
    mod = SyntaxModule()
    
    #print mod.eval_expr("len__gt","ola",10)
    #print mod.eval_hash({"x":"odadad"}, {"x__len__gt":1, "x__len__lt":10})

    ctx = {"language":"pt", "text":"ola mundo"}
    ctx["abc"]=["a","b","c"]

    #action = {"language":"es"}
    action = {"p4":444, "not": {"language":"es"}, "p3":303}
    #action = {"or": [{"language":"es"}, {"language":"pt"}]}
    #action = {"language__match":"es|pt", "p1":1,"p2":20}

    #action = {"web":"http://www.ola.com/{text__quote}"}

    #action = {"title":"coisas","submenu":[{"repeat":"x {abc}", "title":"olá {x}"}]}
    #result = mod._eval_hash(ctx, action)
    #print "RESULT",result

    #actions = [{"repeat":"x {abc}", "title":"olá {x}"}]
    #print "RESULT",mod._eval_list(ctx, actions)
    print(mod._eval_expr(ctx, "text", ""))
    print(mod._replace_vars(ctx,"{text}"))
