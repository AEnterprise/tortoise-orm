from tests.testmodels import Event, NoID, Team, Tournament
from tortoise.contrib import test
from tortoise.exceptions import (
    ConfigurationError,
    DoesNotExist,
    MultipleObjectsReturned,
    OperationalError,
)


class TestModelMethods(test.TestCase):
    async def setUp(self):
        self.mdl = await Tournament.create(name="Test")
        self.mdl2 = Tournament(name="Test")
        self.cls = Tournament

    async def test_save(self):
        oldid = self.mdl.id
        await self.mdl.save()
        self.assertEqual(self.mdl.id, oldid)

    def test_construct_custom_id(self):
        with self.assertRaisesRegex(ValueError, "id is DB generated"):
            self.cls(id=218028, name="Test")

    async def test_save_custom_id(self):
        with self.assertRaisesRegex(ValueError, "id is DB generated"):
            await self.cls.create(id=218028, name="Test")

    async def test_save_full(self):
        self.mdl.name = "TestS"
        self.mdl.desc = "Something"
        await self.mdl.save()
        n_mdl = await self.cls.get(id=self.mdl.id)
        self.assertEqual(n_mdl.name, "TestS")
        self.assertEqual(n_mdl.desc, "Something")

    async def test_save_partial(self):
        self.mdl.name = "TestS"
        self.mdl.desc = "Something"
        await self.mdl.save(update_fields=["desc"])
        n_mdl = await self.cls.get(id=self.mdl.id)
        self.assertEqual(n_mdl.name, "Test")
        self.assertEqual(n_mdl.desc, "Something")

    async def test_create(self):
        mdl = self.cls(name="Test2")
        self.assertIsNone(mdl.id)
        await mdl.save()
        self.assertIsNotNone(mdl.id)

    async def test_delete(self):
        mdl = await self.cls.get(name="Test")
        self.assertEqual(self.mdl.id, mdl.id)

        await self.mdl.delete()

        with self.assertRaises(DoesNotExist):
            await self.cls.get(name="Test")

        with self.assertRaises(OperationalError):
            await self.mdl2.delete()

    def test_str(self):
        self.assertEqual(str(self.mdl), "Test")

    def test_repr(self):
        self.assertEqual(repr(self.mdl), f"<Tournament: {self.mdl.id}>")
        self.assertEqual(repr(self.mdl2), "<Tournament>")

    def test_hash(self):
        self.assertEqual(hash(self.mdl), self.mdl.id)
        with self.assertRaises(TypeError):
            hash(self.mdl2)

    async def test_eq(self):
        mdl = await self.cls.get(name="Test")
        self.assertEqual(self.mdl, mdl)

    async def test_get_or_create(self):
        mdl, created = await self.cls.get_or_create(name="Test")
        self.assertFalse(created)
        self.assertEqual(self.mdl, mdl)
        mdl, created = await self.cls.get_or_create(name="Test2")
        self.assertTrue(created)
        self.assertNotEqual(self.mdl, mdl)
        mdl2 = await self.cls.get(name="Test2")
        self.assertEqual(mdl, mdl2)

    async def test_first(self):
        mdl = await self.cls.first()
        self.assertEqual(self.mdl.id, mdl.id)

    async def test_filter(self):
        mdl = await self.cls.filter(name="Test").first()
        self.assertEqual(self.mdl.id, mdl.id)
        mdl = await self.cls.filter(name="Test2").first()
        self.assertIsNone(mdl)

    async def test_all(self):
        mdls = list(await self.cls.all())
        self.assertEqual(len(mdls), 1)
        self.assertEqual(mdls, [self.mdl])

    async def test_get(self):
        mdl = await self.cls.get(name="Test")
        self.assertEqual(self.mdl.id, mdl.id)

        with self.assertRaises(DoesNotExist):
            await self.cls.get(name="Test2")

        await self.cls.create(name="Test")

        with self.assertRaises(MultipleObjectsReturned):
            await self.cls.get(name="Test")


class TestModelMethodsNoID(TestModelMethods):
    async def setUp(self):
        self.mdl = await NoID.create(name="Test")
        self.mdl2 = NoID(name="Test")
        self.cls = NoID

    def test_str(self):
        self.assertEqual(str(self.mdl), "<NoID>")

    def test_repr(self):
        self.assertEqual(repr(self.mdl), f"<NoID: {self.mdl.id}>")
        self.assertEqual(repr(self.mdl2), "<NoID>")


class TestModelConstructor(test.TestCase):
    def test_null_in_nonnull_field(self):
        with self.assertRaisesRegex(ValueError, "name is non nullable field, but null was passed"):
            Event(name=None)

    def test_rev_fk(self):
        with self.assertRaisesRegex(
            ConfigurationError,
            "You can't set backward relations through init, change related model instead",
        ):
            Tournament(name="a", events=[])

    def test_m2m(self):
        with self.assertRaisesRegex(
            ConfigurationError, "You can't set m2m relations through init, use m2m_manager instead"
        ):
            Event(name="a", participants=[])

    def test_rev_m2m(self):
        with self.assertRaisesRegex(
            ConfigurationError, "You can't set m2m relations through init, use m2m_manager instead"
        ):
            Team(name="a", events=[])

    def test_fk_unsaved(self):
        with self.assertRaisesRegex(OperationalError, "You should first call .save()"):
            Event(name="a", tournament=Tournament(name="a"))

    async def test_fk_saved(self):
        Event(name="a", tournament=await Tournament.create(name="a"))
